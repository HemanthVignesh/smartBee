"""Email Processing Pipeline"""

from sqlalchemy.orm import Session
from app.models.email import Email
from app.models.analysis import EmailAnalysis
from app.models.decision import Decision
from app.models.action import SuggestedAction

from app.services.ai_engine.intent_detector import IntentDetector
from app.services.ai_engine.entity_extractor import EntityExtractor
from app.services.ai_engine.summarizer import EmailSummarizer
from app.services.ai_engine.priority_scorer import PriorityScorer
import logging

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Complete email processing pipeline"""
    
    def __init__(self, db: Session):
        self.db = db
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.summarizer = EmailSummarizer()
        self.priority_scorer = PriorityScorer()
    
    def process_email(self, email_id: str, force: bool = False) -> dict:
        """Process email through AI pipeline"""
        email = self.db.query(Email).filter_by(id=email_id).first()
        if not email:
            return {"error": "Email not found"}
            
        if not force and email.category != "primary":
            return {"message": "Email skipped: only primary category emails are processed through AI pipeline."}
        
        try:
            intent_result = self.intent_detector.detect(
                email.subject, email.body
            )
            
            entities = self.entity_extractor.extract(email.subject, email.body)
            summary = self.summarizer.summarize(email.body)
            priority_result = self.priority_scorer.score(
                email.body, intent_result.get('intent', 'general')
            )
            
            # Store analysis
            analysis = EmailAnalysis(
                email_id=email.id,
                intent=intent_result.get('intent', 'general'),
                priority=priority_result,
                confidence=intent_result.get('confidence', 0.5),
                summary=summary,
                entities=entities
            )
            self.db.add(analysis)
            self.db.commit()
            
            # Create decision
            decision = Decision(
                email_id=email.id,
                decision_type=intent_result.get('intent', 'general'),
                rationale=intent_result.get('reasoning', 'AI analysis')
            )
            self.db.add(decision)
            self.db.commit()
            self.db.refresh(decision)
            
            # Create suggested actions
            actions = self._generate_actions(decision, intent_result, entities, email)
            for action_data in actions:
                action = SuggestedAction(
                    decision_id=decision.id,
                    action_type=action_data['type'],
                    payload=action_data['payload'],
                    status='pending'
                )
                self.db.add(action)
            
            self.db.commit()
            
            return {
                "email_id": email.id,
                "analysis_id": analysis.id,
                "decision_id": decision.id,
                "intent": intent_result.get('intent'),
                "priority": priority_result
            }
        
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            self.db.rollback()
            return {"error": str(e)}
    
    def _generate_actions(self, decision, intent_result, entities, email) -> list:
        """Generate action suggestions based on intent"""
        actions = []
        
        intent = intent_result.get('intent', 'general')
        needs_reply = intent_result.get('needs_reply', False)
        
        if intent == 'meeting_request':
            actions.append({
                'type': 'create_calendar_event',
                'payload': {
                    'suggested_date': entities.get('dates', ['TBD'])[0] if entities.get('dates') else 'TBD',
                    'suggested_time': entities.get('times', ['TBD'])[0] if entities.get('times') else 'TBD'
                }
            })
        
        if needs_reply:
            from app.services.ai_engine.reply_generator import generate_replies
            priority = "medium" # Default/fallback priority
            reply = generate_replies(email.body, intent, priority, entities)
            actions.append({
                'type': 'generate_reply',
                'payload': {
                    'tone': 'professional',
                    'draft': reply,
                    'replies': [reply],
                    'to': 'hemanthvignesh27@gmail.com',
                    'subject': f"Re: {email.subject or 'Inquiry'}"
                }
            })
        
        return actions