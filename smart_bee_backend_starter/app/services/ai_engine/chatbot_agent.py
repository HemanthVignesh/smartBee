import json
import logging
import uuid
import re
import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.models.email import Email
from app.models.action import SuggestedAction
from app.models.analysis import EmailAnalysis
from app.models.chat_history import ChatHistory
from app.services.ai_engine.llm_client import LLMClient
from app.services.executors.calendar_executor import create_calendar_event

logger = logging.getLogger(__name__)

class ChatbotAgent:
    """
    AI-powered Chatbot Agent that can interpret user intents and execute tools.
    Supports: finding unread emails, summarizing emails, drafting replies,
    scheduling follow-up emails, showing today's schedule, and scheduling Google Meet meetings.
    """

    def __init__(self):
        self.llm = LLMClient()

    def _is_refusal(self, text: str) -> bool:
        """
        Check if the LLM output is a refusal message or a generic unhelpful response.
        Also check if the LLM output contains raw JSON representing tool calls during formatting step.
        """
        text_lower = text.lower()
        refusal_keywords = [
            "sorry", "can't assist", "cannot assist", "unable to assist", 
            "don't have access", "cannot help", "can't help", "as an ai",
            "cannot perform", "i apologize", "please share the list",
            "please provide the list", "can you please share", "provide the emails",
            "copy and paste"
        ]
        if any(kw in text_lower for kw in refusal_keywords):
            return True
            
        # If it's asking the user to provide the emails instead of showing summaries/schedules
        if "share the" in text_lower and "email" in text_lower:
            return True
        if "provide the" in text_lower and "email" in text_lower:
            return True
            
        # If the output looks like a JSON block representing a tool call
        if '"tool_call"' in text_lower or '"arguments"' in text_lower or (text.strip().startswith("{") and text.strip().endswith("}")):
            return True
            
        return False

    def _match_early_heuristics(self, user_message: str) -> tuple[str, dict] | None:
        """
        Pre-parse user intent using an expanded natural language pattern library.
        Handles informal/casual phrasing, typos, and multi-intent sentences.
        Returns (tool_name, arguments) if matched, or None to fall through to LLM.
        """
        msg_lower = user_message.lower().strip()

        # ──────────────────────────────────────────────
        # 1. FIND UNREAD EMAILS
        # Matches: "unread", "new emails", "check my mail", "what's new", "any new messages"
        # ──────────────────────────────────────────────
        unread_patterns = [
            r"\bunread\b", r"\bnew email", r"\bnew messages?",
            r"what.?s new", r"any new", r"check my (mail|inbox|email)",
            r"did (i|anyone) (get|receive|send)",
            r"show me (new|latest|recent) (mails?|emails?|messages?)",
            r"(have i|do i have) (any )?(new|unread|pending) (mails?|emails?|messages?)",
            r"\bunprocessed\b", r"\bpending emails\b", r"what emails? (do i|have i)",
            r"my (recent|latest|new) emails?",
        ]
        if any(re.search(p, msg_lower) for p in unread_patterns):
            return "find_unread_emails", {}

        # ──────────────────────────────────────────────
        # 2. SHOW TODAY'S SCHEDULE / CALENDAR
        # Matches: "today's schedule", "what meetings do I have", "my calendar", "agenda"
        # ──────────────────────────────────────────────
        schedule_view_patterns = [
            r"today.?s (schedule|agenda|calendar|meetings?|events?)",
            r"(schedule|agenda|calendar|meetings?|events?) (today|for today)",
            r"what (meetings?|events?|calls?) (do i have|are scheduled|are happening) (today|this (morning|afternoon|evening))",
            r"(show|display|list) (my )?(today.?s )?(schedule|calendar|meetings?|events?)",
            r"what.?s (on my )?(schedule|calendar|agenda) (today|now)",
            r"(do i|have i) (have|got) (any )?(meetings?|events?|calls?) (today|scheduled)",
            r"am i (busy|free|available) today",
            r"today.?s events?|upcoming events?",
        ]
        if any(re.search(p, msg_lower) for p in schedule_view_patterns):
            return "show_today_schedule", {}

        # ──────────────────────────────────────────────
        # 3. SCHEDULE A MEETING / GOOGLE MEET
        # Matches: "schedule/book/set up a meeting/call/appointment"
        # ──────────────────────────────────────────────
        meeting_action_patterns = [
            r"(schedule|book|set up|arrange|organize|create|add) (a |an )?(meeting|meet|call|appointment|discussion|session|zoom|google meet)",
            r"(can you )?(book|schedule|set up) (a )?(meeting|call|meet|appointment)",
            r"(let.?s|i want to|i need to|i.?d like to) (have|schedule|set up|organize|arrange) (a )?(meeting|call|discussion)",
            r"fix (a |an )?(meeting|call|time|slot|appointment)",
            r"create (a |an )?(calendar event|meeting|event|appointment|google meet|meet)",
        ]
        if any(re.search(p, msg_lower) for p in meeting_action_patterns):
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
            recipient = emails[0] if emails else "hemanthvignesh27@gmail.com"
            
            # Parse date
            date_str = None
            if re.search(r"\bday after tomorrow\b", msg_lower):
                date_str = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            elif "tomorrow" in msg_lower:
                date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif re.search(r"\bthis (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", msg_lower):
                day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                day_match = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", msg_lower)
                if day_match:
                    target_day = day_names.index(day_match.group(1))
                    today = datetime.now()
                    days_ahead = (target_day - today.weekday()) % 7 or 7
                    date_str = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            elif "next week" in msg_lower:
                date_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            elif "today" in msg_lower:
                date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_message)
                if date_match:
                    date_str = date_match.group(0)
                else:
                    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    
            # Parse time — handle "11am", "3:30pm", "at 2pm", "at noon", "in the morning"
            time_str = "11:00"
            if "noon" in msg_lower or "12pm" in msg_lower or "midday" in msg_lower:
                time_str = "12:00"
            elif "midnight" in msg_lower:
                time_str = "00:00"
            elif re.search(r"in the (morning|afternoon|evening)", msg_lower):
                period_m = re.search(r"in the (morning|afternoon|evening)", msg_lower)
                if period_m:
                    period = period_m.group(1)
                    time_str = "09:00" if period == "morning" else ("15:00" if period == "afternoon" else "18:00")
            else:
                # Try "3:30pm" or "11:00"
                time_match = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", msg_lower)
                if time_match:
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    am_pm = time_match.group(3)
                    if am_pm == "pm" and hours < 12:
                        hours += 12
                    elif am_pm == "am" and hours == 12:
                        hours = 0
                    time_str = f"{hours:02d}:{minutes:02d}"
                else:
                    # Try "at 11am" or "11 am" or "3pm"
                    ampm_match = re.search(r"\bat?\s*(\d{1,2})\s*(am|pm)\b", msg_lower)
                    if ampm_match:
                        hours = int(ampm_match.group(1))
                        am_pm = ampm_match.group(2)
                        if am_pm == "pm" and hours < 12:
                            hours += 12
                        elif am_pm == "am" and hours == 12:
                            hours = 0
                        time_str = f"{hours:02d}:00"
                    
            # Title & Agenda — extract topic from "about X", "regarding X", "for X" phrases
            title = "Smart Bee Calendar Meeting"
            agenda = None
            topic_patterns = [
                r"\b(regarding|about|on|for|re:?)\s+([^,.@\n]+)",
                r"\bconcerning\s+([^,.@\n]+)",
                r"\bdiscuss(?:ion)?\s+([^,.@\n]+)",
            ]
            for tp in topic_patterns:
                topic_match = re.search(tp, user_message, re.IGNORECASE)
                if topic_match:
                    raw_text = topic_match.group(topic_match.lastindex).strip()
                    # Clean up stopwords from topic
                    for stopword in ["tomorrow", "today", "yesterday", "next week", "this week",
                                     "morning", "afternoon", "evening", "at ", "pm", "am",
                                     "a meeting", "the meeting", "meeting", recipient.split("@")[0]]:
                        raw_text = re.sub(re.escape(stopword), "", raw_text, flags=re.IGNORECASE)
                    raw_text = re.sub(r"\s+", " ", raw_text).strip(" ,.-")
                    if len(raw_text) > 3:
                        title = f"Smart Bee: {raw_text[:60]}"
                        agenda = raw_text[:120]
                        break
            
            return "schedule_meeting", {
                "recipient_email": recipient,
                "title": title,
                "date": date_str,
                "time": time_str,
                "agenda": agenda
            }

        # ──────────────────────────────────────────────
        # 4. SCHEDULE FOLLOW-UP / SEND EMAIL LATER
        # ──────────────────────────────────────────────
        followup_patterns = [
            r"\bfollow[- ]?up\b",
            r"(send|shoot|write) (a |an )?(follow[- ]?up|reminder|nudge)",
            r"remind (me|them|him|her) (to|about|that)",
            r"(schedule|queue|set up|plan) (a |an )?(email|message|mail)",
            r"(send|shoot) (an? )?(email|message|mail) (later|tomorrow|next|in|after)",
            r"(ping|email|message|mail) (them|him|her|the team) (later|tomorrow|next week)",
        ]
        if any(re.search(p, msg_lower) for p in followup_patterns):
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
            recipient = emails[0] if emails else "hemanthvignesh27@gmail.com"
            
            # Parse delay
            delay_hours = 24.0
            hours_match = re.search(r"(\d+(\.\d+)?)\s*hours?", msg_lower)
            days_match = re.search(r"(\d+(\.\d+)?)\s*days?", msg_lower)
            if hours_match:
                delay_hours = float(hours_match.group(1))
            elif days_match:
                delay_hours = float(days_match.group(1)) * 24
            elif "tomorrow" in msg_lower:
                delay_hours = 24.0
            elif "next week" in msg_lower:
                delay_hours = 168.0

            # Extract subject hint
            subject = "Follow up"
            sub_match = re.search(r"(subject|about|re:|regarding)[:\s]+([^,.]+)", user_message, re.IGNORECASE)
            if sub_match:
                subject = sub_match.group(2).strip()[:80]

            return "schedule_follow_up", {
                "recipient_email": recipient,
                "subject": subject,
                "body": f"Hi,\n\nJust following up regarding our previous conversation about {subject}.\n\nBest regards,\nHemanth",
                "delay_hours": delay_hours
            }

        # ──────────────────────────────────────────────
        # 5. DRAFT / WRITE A REPLY
        # Matches: "draft a reply", "write back to", "respond to", "reply to"
        # ──────────────────────────────────────────────
        reply_patterns = [
            r"(draft|write|compose|prepare|craft) (a |an )?(reply|response|email|message|mail)",
            r"(reply|respond|write back|get back) (to|for)",
            r"(can you )?(reply|respond) (to|on behalf of)",
            r"\breply to\b", r"\brespond to\b", r"\bdraft a\b", r"\bwrite back\b",
            r"(email|message|mail|write) (back|them|him|her) (back|saying|that|with)",
            r"(let|tell) them (know|that|i)",
        ]
        if any(re.search(p, msg_lower) for p in reply_patterns):
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
            sender = emails[0] if emails else None
            
            # Try to extract sender name if no email
            if not sender:
                name_match = re.search(r"\b(to|from|for|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", user_message)
                if name_match and name_match.group(2).lower() not in ["me", "my", "the", "a", "an"]:
                    sender = name_match.group(2)
            
            # Extract what to say
            reply_content = "I'll get back to you shortly regarding this matter."
            say_match = re.search(
                r"\b(say(?:ing)?|tell(?:ing)? them?|write|mention(?:ing)?|that)[:\s]+(.+?)(?:[.!?]|$)",
                user_message, re.IGNORECASE
            )
            if say_match:
                reply_content = say_match.group(2).strip()
                
            return "draft_reply", {
                "sender": sender,
                "reply_content": reply_content
            }

        # ──────────────────────────────────────────────
        # 6. SUMMARIZE EMAILS / INBOX / MESSAGES
        # Matches: "summarize my inbox", "what are my emails about", "give me a summary"
        # ──────────────────────────────────────────────
        summarize_patterns = [
            r"(summar(?:ize|ise|y)|overview|digest|rundown|recap|brief)",
            r"what.?s (in|going on in|happening in) my (inbox|mail|emails?)",
            r"(show|tell|give) me (my )?(inbox|emails?|mail|messages?)",
            r"what (emails?|mails?|messages?) (did i|have i|do i) (get|receive|have|got)",
            r"(check|look at|read|open|view|go through) my (inbox|emails?|mail|messages?)",
            r"(what|any) (important |urgent )?(emails?|messages?|mails?) (today|this (week|morning|afternoon))",
            r"catch me up (on |with )?(my )?(emails?|inbox|mail)",
            r"what.?s new (in )?(my )?(inbox|emails?|mail)",
        ]
        if any(re.search(p, msg_lower) for p in summarize_patterns):
            category = None
            for cat in ["primary", "updates", "forums"]:
                if cat in msg_lower:
                    category = cat
            
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
            sender = emails[0] if emails else None
            if not sender:
                from_match = re.search(r"\bfrom\s+([A-Z][a-z]+)\b", user_message)
                if from_match:
                    sender = from_match.group(1)
                    
            limit = 5
            limit_match = re.search(r"\b(last|recent|top|first)\s+(\d+)\b", msg_lower)
            if limit_match:
                limit = int(limit_match.group(2))
            elif re.search(r"\ball\b", msg_lower):
                limit = 10
                
            return "summarize_emails", {
                "sender": sender,
                "category": category,
                "limit": limit
            }

        return None

    def _generate_conversational_reply(self, user_message: str) -> str | None:
        """
        Handle common conversational messages that don't require tool execution.
        Returns a friendly reply string, or None to fall through to LLM.
        """
        msg_lower = user_message.lower().strip()
        
        # IST time/date context
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_offset)
        
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy", "sup", "what's up"]
        if any(msg_lower.startswith(g) or msg_lower == g for g in greetings):
            time_greeting = "Good morning" if now_ist.hour < 12 else ("Good afternoon" if now_ist.hour < 17 else "Good evening")
            return (
                f"{time_greeting}! 👋 I'm **Smart Bee AI**, your intelligent email assistant.\n\n"
                "Here's what I can do for you:\n"
                "- 📥 **Find & summarize** your inbox (primary emails only)\n"
                "- ✍️ **Draft smart replies** to emails\n"
                "- 📅 **Schedule meetings** with Google Meet\n"
                "- ⏰ **Set up follow-ups** and reminders\n"
                "- 🗓️ **Show today's calendar**\n\n"
                "What would you like to do today?"
            )
        
        # Date & time queries
        if any(kw in msg_lower for kw in ["what date", "today's date", "what day", "current date", "what time", "current time", "what is the date", "what is today"]):
            date_str = now_ist.strftime("%A, %B %d, %Y")
            time_str = now_ist.strftime("%I:%M %p IST")
            return (
                f"🗓️ **Today is {date_str}**\n"
                f"⏰ **Current time: {time_str}** (Asia/Kolkata)\n\n"
                "Is there anything I can help you schedule or look up?"
            )
        
        # Who are you / what are you
        if any(kw in msg_lower for kw in ["who are you", "what are you", "tell me about yourself", "introduce yourself"]):
            return (
                "I'm **Smart Bee AI** 🐝 — your intelligent email and calendar assistant!\n\n"
                "I'm built into the **Smart Bee** platform and I can:\n"
                "- Read and summarize your **primary inbox** emails\n"
                "- Draft professional **email replies** using AI\n"
                "- **Schedule Google Meet** meetings and send invitations\n"
                "- Set up **follow-up emails** for future delivery\n"
                "- Show your **today's calendar** and meetings\n\n"
                "> I only analyze **Primary** emails — promotions, social, and spam are excluded from AI analysis unless you specifically ask."
            )
        
        if any(kw in msg_lower for kw in ["thank", "thanks", "thx", "cheers", "great", "awesome", "perfect", "nice", "good job", "well done"]):
            return "You're welcome! 😊 Is there anything else I can help you with?"
        
        if any(kw in msg_lower for kw in ["help", "what can you do", "how do i", "what do you", "capabilities", "features"]):
            return (
                "Here's everything I can help you with:\n\n"
                "**📥 Email Management**\n"
                "- Find unread/new emails\n"
                "- Summarize your primary inbox\n"
                "- Draft professional replies\n\n"
                "**📅 Scheduling**\n"
                "- Schedule Google Meet meetings\n"
                "- Create calendar events\n"
                "- Set up follow-up emails\n\n"
                "**🤖 Smart Actions**\n"
                "- Auto-detect meeting requests in emails\n"
                "- Show today's schedule\n\n"
                "> **Note:** AI analysis is only applied to **Primary** emails. Promotions, Social, and Spam are kept separate."
            )
        
        if any(kw in msg_lower for kw in ["bye", "goodbye", "see you", "later", "ciao", "take care"]):
            return "Goodbye! 👋 Come back anytime you need help with your emails. Stay productive! 🐝"
        
        return None


    def _offline_format_result(self, tool_name: str, tool_args: dict, tool_result: dict) -> str:
        """
        Produce a high-end, premium markdown response offline if LLM formatting fails or refuses.
        """
        if "error" in tool_result:
            return f"❌ **Error executing action**: {tool_result['error']}"
        
        # Normalize tool name to canonical form for matching
        tn = str(tool_name).strip().lower().replace("-", "_").replace(" ", "_")
        if tn in ["summarize_emails", "summary_emails", "summarise_emails", "get_emails", "emails", "summarize", "summary"]:
            tn = "summarize_emails"
        elif tn in ["find_unread_emails", "unread_emails", "find_unread", "unread"]:
            tn = "find_unread_emails"
        elif tn in ["draft_reply", "reply_email", "reply", "draft"]:
            tn = "draft_reply"
        elif tn in ["show_today_schedule", "today_schedule", "schedule_today", "show_schedule", "schedule", "today_meetings"]:
            tn = "show_today_schedule"
        elif tn in ["schedule_meeting", "create_meeting", "meeting", "book_meeting"]:
            tn = "schedule_meeting"
        elif tn in ["schedule_follow_up", "follow_up"]:
            tn = "schedule_follow_up"
            
        if tn == "find_unread_emails":
            unread_count = tool_result.get("unread_count", 0)
            if unread_count == 0:
                return "📥 **All caught up!** You have no unread or unprocessed emails in your inbox."
            
            response = f"📥 **You have {unread_count} unread email(s):**\n\n"
            for email in tool_result.get("emails", []):
                try:
                    dt = datetime.fromisoformat(email["received_at"])
                    time_str = dt.strftime("%b %d, %H:%M")
                except Exception:
                    time_str = email["received_at"]
                response += f"* **From:** `{email['sender']}` | **Subject:** *{email['subject']}* | *({time_str})*\n"
            return response
            
        elif tn == "summarize_emails":
            count = tool_result.get("count", 0)
            if count == 0:
                return "🔍 **No recent emails found** matching your search criteria."
                
            filters = tool_result.get("filters", {})
            filter_desc = []
            if filters.get("sender"):
                filter_desc.append(f"from `{filters['sender']}`")
            if filters.get("category"):
                filter_desc.append(f"in category `{filters['category'].capitalize()}`")
            filter_str = f" ({', '.join(filter_desc)})" if filter_desc else ""
            
            response = f"📊 **Here is a summary of your recent emails{filter_str}:**\n\n"
            for email in tool_result.get("emails", []):
                response += f"✉️ **Sender:** `{email['sender']}` | **Subject:** *{email['subject']}*\n"
                response += f"📝 **Summary:** {email['summary']}\n\n"
                response += "---\n\n"
            if response.endswith("---\n\n"):
                response = response[:-6]
            return response
            
        elif tn == "draft_reply":
            response = "✉️ **Draft Reply Prepared successfully!**\n\n"
            response += f"* **To:** `{tool_result.get('to')}`\n"
            response += f"* **Subject:** *{tool_result.get('subject')}*\n"
            response += f"* **Status:** `Pending Approval` (You can approve this under Scheduled Actions)\n\n"
            response += "📝 **Draft Content:**\n"
            response += f"```\n{tool_result.get('body')}\n```"
            return response
            
        elif tn == "show_today_schedule":
            count = tool_result.get("count", 0)
            today_date = tool_result.get("today_date", "")
            if count == 0:
                return f"📅 **No meetings scheduled** for today ({today_date}). Enjoy your open schedule!"
                
            response = f"📅 **Your Schedule for Today ({today_date}):**\n\n"
            for idx, mtg in enumerate(tool_result.get("meetings", []), 1):
                meet_part = f" | [Join Google Meet]({mtg['meet_link']})" if mtg.get("meet_link") else ""
                response += f"{idx}. ⏰ **{mtg['time']}** - **{mtg['title']}** (Duration: {mtg['duration']}){meet_part}\n"
            return response
            
        elif tn == "schedule_meeting":
            response = "📅 **Meeting Scheduled Successfully!**\n\n"
            response += f"* **Title:** *{tool_result.get('title')}*\n"
            response += f"* **Recipient:** `{tool_result.get('recipient')}`\n"
            response += f"* **Date:** `{tool_result.get('date')}`\n"
            response += f"* **Time:** `{tool_result.get('time')} (Asia/Kolkata)`\n\n"
            if tool_result.get("meet_link"):
                response += f"🎥 **Google Meet:** [Join Meeting]({tool_result.get('meet_link')})\n"
            if tool_result.get("event_link"):
                response += f"🔗 **Calendar Event:** [View Event]({tool_result.get('event_link')})\n\n"
            response += "📨 An automated email invitation with the Google Meet details has been queued and sent to the recipient."
            return response
            
        elif tn == "schedule_follow_up":
            response = "⏰ **Follow-up Email Scheduled Successfully!**\n\n"
            response += f"* **To:** `{tool_result.get('recipient')}`\n"
            response += f"* **Subject:** *{tool_result.get('subject')}*\n"
            time_str = tool_result.get("scheduled_time", "")
            try:
                dt = datetime.fromisoformat(time_str)
                time_str = dt.strftime("%b %d, %Y at %H:%M UTC")
            except Exception:
                pass
            response += f"* **Scheduled Send Time:** `{time_str}`\n"
            response += f"* **Status:** `Scheduled`"
            return response
            
        return f"✅ **Tool Executed successfully** ({tool_name}).\n\nResult:\n```json\n{json.dumps(tool_result, indent=2)}\n```"

    def _get_formatter_prompt(self, tool_name: str, tool_args: dict, tool_result: dict, user_message: str) -> str:
        """Construct specialized formatting prompt based on the executed tool and user query."""
        name_clean = str(tool_name).strip().lower().replace("-", "_").replace(" ", "_")
        
        # 1. summarize_emails / search
        if name_clean in ["summarize_emails", "summary_emails", "summarise_emails", "get_emails", "emails", "summarize", "summary"]:
            context_str = ""
            for e in tool_result.get("emails", []):
                context_str += f"From: {e['sender']}\nSubject: {e['subject']}\nCategory: {e['category']}\nContent/Summary: {e['summary']}\n\n"
            
            is_question = any(q_word in user_message.lower() for q_word in ["what", "why", "when", "who", "where", "how", "did", "does", "is there", "do i", "are there", "can you tell", "tell me"])
            if is_question:
                return (
                    f"Answer the user's question directly, concisely, and conversationally using the email context below. "
                    f"Mention the sender and subject if relevant. Do NOT output JSON.\n\n"
                    f"Email Context:\n{context_str if context_str else 'No relevant emails found.'}\n"
                    f"Question: {user_message}\n\n"
                    f"Answer:"
                )
            else:
                return (
                    f"Summarize the following emails clearly, focusing on key decisions and actions. Do NOT output JSON.\n\n"
                    f"Email Context:\n{context_str if context_str else 'No emails found.'}\n\n"
                    f"Summary:"
                )
                
        # 2. find_unread_emails
        elif name_clean in ["find_unread_emails", "unread_emails", "find_unread", "unread"]:
            emails_str = ""
            for e in tool_result.get("emails", []):
                emails_str += f"- From: {e['sender']} | Subject: {e['subject']}\n"
            return (
                f"The user wants to see unread or unprocessed emails. Summarize the unread emails listed below. "
                f"If there are none, tell them they are all caught up.\n\n"
                f"Unread Emails Data:\n{emails_str if emails_str else 'No unread emails.'}\n\n"
                f"Response:"
            )
            
        # 3. draft_reply
        elif name_clean in ["draft_reply", "reply_email", "reply", "draft"]:
            return (
                f"Tell the user that a reply has been drafted and is pending approval in scheduled actions. "
                f"Show the draft details and the drafted content clearly. Do NOT output JSON.\n\n"
                f"Draft details:\n"
                f"To: {tool_result.get('to')}\n"
                f"Subject: {tool_result.get('subject')}\n"
                f"Draft Body:\n{tool_result.get('body')}\n\n"
                f"Response:"
            )
            
        # 4. show_today_schedule
        elif name_clean in ["show_today_schedule", "today_schedule", "schedule_today", "show_schedule", "schedule", "today_meetings"]:
            mtgs_str = ""
            for idx, mtg in enumerate(tool_result.get("meetings", []), 1):
                mtgs_str += f"{idx}. Time: {mtg['time']} | Title: {mtg['title']} | Join link: {mtg.get('meet_link')}\n"
            return (
                f"Show the user their schedule for today. List the meetings and their Google Meet links if available. "
                f"If there are no meetings, tell them they have an open schedule. Do NOT output JSON.\n\n"
                f"Today's Meetings:\n{mtgs_str if mtgs_str else 'No meetings scheduled today.'}\n\n"
                f"Response:"
            )
            
        # 5. schedule_meeting
        elif name_clean in ["schedule_meeting", "create_meeting", "meeting", "book_meeting"]:
            return (
                f"Formulate a premium confirmation message showing that the meeting has been scheduled. "
                f"Directly list the recipient email, date, time, and Google Meet/Calendar links. Do NOT output JSON.\n\n"
                f"Meeting Details:\n"
                f"Title: {tool_result.get('title')}\n"
                f"Recipient: {tool_result.get('recipient')}\n"
                f"Date & Time: {tool_result.get('date')} at {tool_result.get('time')} (Asia/Kolkata)\n"
                f"Google Meet: {tool_result.get('meet_link')}\n"
                f"Calendar Event: {tool_result.get('event_link')}\n\n"
                f"Response:"
            )
            
        # 6. schedule_follow_up
        elif name_clean in ["schedule_follow_up", "follow_up"]:
            return (
                f"Confirm that the email has been scheduled for future delivery. "
                f"Show the recipient, subject, and scheduled send time. Do NOT output JSON.\n\n"
                f"Follow-up Details:\n"
                f"Recipient: {tool_result.get('recipient')}\n"
                f"Subject: {tool_result.get('subject')}\n"
                f"Scheduled Send Time: {tool_result.get('scheduled_time')}\n\n"
                f"Response:"
            )
            
        else:
            return (
                f"Summarize the following execution result for the user's request. Do NOT output JSON.\n\n"
                f"User Request: {user_message}\n"
                f"Result: {json.dumps(tool_result, indent=2)}\n\n"
                f"Response:"
            )

    def handle_chat(self, user_message: str, db: Session, session_id: str = "default_session") -> str:
        """
        Process the user message, execute tools if required, and return the response.
        """
        try:
            # 0. Early heuristics matching to bypass LLM latency/refusals
            matched_tool = self._match_early_heuristics(user_message)
            if matched_tool:
                tool_name, tool_args = matched_tool
                logger.info(f"Early heuristic matched tool '{tool_name}' with arguments: {tool_args}")
                tool_result = self._execute_tool(db, tool_name, tool_args)
                
                # Attempt LLM formatting
                try:
                    formatter_prompt = self._get_formatter_prompt(tool_name, tool_args, tool_result, user_message)
                    formatted_reply = self.llm.generate_completion(
                        formatter_prompt, 
                        system_prompt="You are Smart Bee assistant. Formulate a final conversational answer for the user based on the tool results.",
                        max_tokens=1000
                    )
                    if self._is_refusal(formatted_reply):
                        logger.warning(f"Formatting LLM refused/failed with refusal message: {formatted_reply}. Using offline formatter.")
                        return self._offline_format_result(tool_name, tool_args, tool_result)
                    return formatted_reply
                except Exception as e:
                    logger.warning(f"Formatting LLM error: {e}. Using offline formatter.")
                    return self._offline_format_result(tool_name, tool_args, tool_result)

            # 0.5. Check for simple conversational replies (greetings, thanks, help, bye)
            conv_reply = self._generate_conversational_reply(user_message)
            if conv_reply:
                logger.info(f"Returning conversational reply for: {user_message[:40]}")
                return conv_reply

            # 1. Fetch recent conversation history for context (up to 6 messages)
            history_entries = db.query(ChatHistory).filter_by(session_id=session_id).order_by(ChatHistory.created_at.desc()).limit(6).all()
            history_entries.reverse()
            chat_history_str = ""
            for entry in history_entries:
                chat_history_str += f"{entry.role.capitalize()}: {entry.content}\n"

            # 2. Build system prompt instructing LLM to output tool calls in structured JSON
            system_prompt = self._get_system_prompt(db)
            prompt = (
                f"Conversation History:\n{chat_history_str}"
                f"User Message: {user_message}\n\n"
                f"Respond with a valid JSON block only."
            )

            # 3. Call the LLM waterfall pipeline
            llm_response = self.llm.generate_completion(prompt, system_prompt=system_prompt)
            
            # 4. Parse the LLM response
            parsed = self._parse_agent_response(llm_response, user_message)
            
            # 5. Execute tool if specified
            tool_call = parsed.get("tool_call")
            thought = parsed.get("thought", "No thought provided.")
            reply = parsed.get("reply", "")

            if tool_call:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                logger.info(f"Agent decided to execute tool '{tool_name}' with arguments: {tool_args}")
                
                tool_result = self._execute_tool(db, tool_name, tool_args)
                
                # Ask LLM to format the tool execution results into a user-friendly conversational response
                try:
                    formatter_prompt = self._get_formatter_prompt(tool_name, tool_args, tool_result, user_message)
                    formatted_reply = self.llm.generate_completion(
                        formatter_prompt, 
                        system_prompt="You are Smart Bee assistant. Formulate a final conversational answer for the user based on the tool results.",
                        max_tokens=1000
                    )
                    if self._is_refusal(formatted_reply):
                        logger.warning(f"Formatting LLM refused response: {formatted_reply}. Using offline formatter.")
                        return self._offline_format_result(tool_name, tool_args, tool_result)
                    return formatted_reply
                except Exception as e:
                    logger.warning(f"Formatting LLM error: {e}. Using offline formatter.")
                    return self._offline_format_result(tool_name, tool_args, tool_result)
            
            # If reply is empty or looks like a JSON dump, provide a helpful fallback
            if not reply or reply.strip().startswith("{"):
                return (
                    "I'm not sure what you're asking. Here are some things I can help with:\n\n"
                    "- 📥 **Summarize your inbox** — *\"Summarize my emails\"*\n"
                    "- 🔍 **Find unread emails** — *\"Show me unread emails\"*\n"
                    "- ✍️ **Draft a reply** — *\"Draft a reply to John\"*\n"
                    "- 📅 **Schedule a meeting** — *\"Book a meeting tomorrow at 3pm\"*\n"
                    "- ⏰ **Set a follow-up** — *\"Follow up with client in 2 hours\"*\n"
                    "- 🗓️ **Today's schedule** — *\"What's on my calendar today?\"*"
                )
            return reply

        except Exception as e:
            logger.error(f"ChatbotAgent handle_chat error: {e}")
            return f"I'm sorry, I encountered an issue processing your request: {str(e)}"

    def _get_system_prompt(self, db: Session) -> str:
        """
        Generate the rich agent instruction prompt listing available tools.
        Includes filtered recent mailbox context with email snippets/summaries.
        """
        # Current date/time in IST for scheduling context
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_offset)
        today_str = now_ist.strftime("%Y-%m-%d")
        tomorrow_str = (now_ist + timedelta(days=1)).strftime("%Y-%m-%d")
        now_str = now_ist.strftime("%A, %B %d, %Y at %I:%M %p IST")

        # Fetch latest 10 emails, excluding promotions, social, and spam
        latest_emails = db.query(Email).filter(
            Email.category.notin_(["promotions", "social", "spam"])
        ).order_by(desc(Email.received_at)).limit(10).all()
        
        recent_context = ""
        if latest_emails:
            recent_context = "\nRecent inbox emails (excluding promotions, social, and spam):\n"
            for email in latest_emails:
                snippet = email.body[:150].replace("\n", " ").strip()
                if email.analysis and email.analysis.summary:
                    snippet = email.analysis.summary[:150].strip()
                recent_context += f"- ID: {email.id} | Category: {email.category} | From: {email.sender} | Subject: {email.subject} | Content: {snippet}\n"

        return f"""You are Smart Bee, the user's advanced AI email and calendar assistant.
You can help the user manage their mailbox and schedule by executing tool operations.

Current Date & Time: {now_str}
Today's Date (YYYY-MM-DD): {today_str}
Tomorrow's Date (YYYY-MM-DD): {tomorrow_str}
Timezone: Asia/Kolkata (IST, UTC+5:30)

To run a tool, you MUST output a JSON object containing the tool name and arguments. Do not output any conversational text or markdown blocks outside the JSON object.

Available Tools:

1. "find_unread_emails"
   Arguments: None
   Use: Find unread or unprocessed emails in the inbox.

2. "summarize_emails"
   Arguments:
     - "sender": (string, optional) filter by sender name or email address
     - "category": (string, optional) filter by category (primary, updates, forums)
     - "limit": (integer, optional, default: 5) max emails to summarize
   Use: Summarize recent emails. Excludes promotions, social, and spam by default.

3. "draft_reply"
   Arguments:
     - "email_id": (string, optional) target email ID
     - "sender": (string, optional) sender name/email to identify the target email
     - "reply_content": (string) body content or instructions for the reply
   Use: Draft a reply to a specific email.

4. "show_today_schedule"
   Arguments: None
   Use: Show meetings, calendar events, or schedule items for today.

5. "schedule_meeting"
   Arguments:
     - "recipient_email": (string) email address to invite
     - "title": (string) meeting title
     - "date": (string, YYYY-MM-DD) meeting date
     - "time": (string, HH:MM) meeting start time
     - "agenda": (string, optional) description/agenda
   Use: Schedule a meeting, create a calendar event with Google Meet link, and automatically queue/send an email invitation to the recipient.

6. "schedule_follow_up"
   Arguments:
     - "recipient_email": (string) recipient email
     - "subject": (string) email subject
     - "body": (string) email body
     - "delay_hours": (float, optional) schedule email to send after this many hours
     - "scheduled_time": (string, YYYY-MM-DD HH:MM, optional) exact send time
   Use: Schedule a follow-up or any email to be sent at a future time.
{recent_context}
If you need to call a tool, your output MUST be this exact JSON format:
{{
  "tool_call": {{
    "name": "tool_name",
    "arguments": {{ ... }}
  }},
  "thought": "Your reasoning steps"
}}

If no tool is needed (e.g. conversational greeting, asking questions about emails in the context, or query not matching any tools), output:
{{
  "tool_call": null,
  "thought": "Your reasoning steps",
  "reply": "Your friendly and detailed reply/answer to the user"
}}
"""

    def _parse_agent_response(self, response_text: str, user_message: str) -> dict:
        """
        Clean and parse the LLM agent response. Includes heuristic fallbacks if JSON fails to parse.
        """
        cleaned = response_text.strip()
        
        # Clean markdown code blocks if present anywhere
        if "```" in cleaned:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
            else:
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            # Try to extract content between outermost matching braces
            try:
                start_idx = cleaned.find("{")
                end_idx = cleaned.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_candidate = cleaned[start_idx:end_idx+1]
                    return json.loads(json_candidate)
            except Exception:
                pass

            logger.warning(f"Failed to parse agent JSON. Raw response: {response_text}. Running heuristics.")
            
            # Heuristic trigger checks in case LLM falls back to raw conversational text
            msg_lower = user_message.lower()
            
            if "unread" in msg_lower or "new email" in msg_lower or "unprocessed" in msg_lower:
                return {
                    "tool_call": {"name": "find_unread_emails", "arguments": {}},
                    "thought": "Fallback trigger: user asked about unread emails."
                }
            elif "summarize" in msg_lower or "summary" in msg_lower or "summarise" in msg_lower:
                category = None
                for cat in ["primary", "promotions", "social", "updates", "forums"]:
                    if cat in msg_lower:
                        category = cat
                return {
                    "tool_call": {"name": "summarize_emails", "arguments": {"category": category}},
                    "thought": "Fallback trigger: user asked for summaries."
                }
            elif ("schedule" in msg_lower or "book" in msg_lower or "calendar" in msg_lower or "set up" in msg_lower or "arrange" in msg_lower) and ("meeting" in msg_lower or "meet" in msg_lower or "call" in msg_lower or "appointment" in msg_lower or "zoom" in msg_lower or "google meet" in msg_lower):
                # Try to extract email using regex
                emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
                recipient = emails[0] if emails else "client@example.com"
                
                # Try to extract date and time
                date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_message)
                time_match = re.search(r"\b\d{1,2}:\d{2}\b", user_message)
                
                date_str = date_match.group(0) if date_match else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                time_str = time_match.group(0) if time_match else "11:00"
                
                return {
                    "tool_call": {
                        "name": "schedule_meeting",
                        "arguments": {
                            "recipient_email": recipient,
                            "title": "Smart Bee Calendar Meeting",
                            "date": date_str,
                            "time": time_str
                        }
                    },
                    "thought": "Fallback trigger: user wants to schedule a meeting."
                }
            elif "schedule" in msg_lower or "follow up" in msg_lower or "follow-up" in msg_lower:
                emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
                recipient = emails[0] if emails else "client@example.com"
                return {
                    "tool_call": {
                        "name": "schedule_follow_up",
                        "arguments": {
                            "recipient_email": recipient,
                            "subject": "Follow up message",
                            "body": "Hi, just following up regarding our discussion.",
                            "delay_hours": 24.0
                        }
                    },
                    "thought": "Fallback trigger: user wants to schedule follow up."
                }
            elif "reply" in msg_lower or "draft" in msg_lower or "tell" in msg_lower or "email back" in msg_lower or "write to" in msg_lower or "respond to" in msg_lower:
                emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
                sender = emails[0] if emails else None
                return {
                    "tool_call": {
                        "name": "draft_reply",
                        "arguments": {
                            "sender": sender,
                            "reply_content": "I will get back to you soon."
                        }
                    },
                    "thought": "Fallback trigger: user wants to draft a reply."
                }
            elif "schedule" in msg_lower or "calendar" in msg_lower or "today" in msg_lower:
                return {
                    "tool_call": {"name": "show_today_schedule", "arguments": {}},
                    "thought": "Fallback trigger: user wants to see their schedule."
                }
                
            return {
                "tool_call": None,
                "thought": "Fallback conversation response.",
                "reply": response_text
            }

    def _execute_tool(self, db: Session, tool_name: str, arguments: dict) -> dict:
        """
        Execute the matching tool function. Normalizes name variations.
        """
        name_clean = str(tool_name).strip().lower().replace("-", "_").replace(" ", "_")
        
        if name_clean in ["find_unread_emails", "unread_emails", "find_unread", "unread"]:
            return self._tool_find_unread_emails(db)
        elif name_clean in ["summarize_emails", "summary_emails", "summarise_emails", "get_emails", "emails", "summarize", "summary"]:
            return self._tool_summarize_emails(db, **arguments)
        elif name_clean in ["draft_reply", "reply_email", "reply", "draft"]:
            return self._tool_draft_reply(db, **arguments)
        elif name_clean in ["show_today_schedule", "today_schedule", "schedule_today", "show_schedule", "schedule", "today_meetings"]:
            return self._tool_show_today_schedule(db)
        elif name_clean in ["schedule_meeting", "create_meeting", "meeting", "book_meeting"]:
            return self._tool_schedule_meeting(db, **arguments)
        elif name_clean in ["schedule_follow_up", "follow_up"]:
            return self._tool_schedule_follow_up(db, **arguments)
        else:
            return {"error": f"Tool '{tool_name}' is not supported."}

    def _tool_find_unread_emails(self, db: Session) -> dict:
        """Find emails where processed == False (excluding promotions, social, and spam by default)"""
        emails = db.query(Email).filter(
            Email.processed == False,
            Email.category.notin_(["promotions", "social", "spam"])
        ).order_by(desc(Email.received_at)).all()
        return {
            "unread_count": len(emails),
            "emails": [
                {
                    "id": email.id,
                    "sender": email.sender,
                    "subject": email.subject,
                    "received_at": email.received_at.isoformat(),
                    "category": email.category
                } for email in emails
            ]
        }

    def _tool_summarize_emails(self, db: Session, sender: str = None, category: str = None, limit: int = 5, **kwargs) -> dict:
        """Retrieve recent emails and summarize them. Supports keyword search if category isn't a standard database category."""
        query = db.query(Email)
        if sender:
            query = query.filter(Email.sender.contains(sender))
        
        # If category is provided, check if it is a valid DB category or a search keyword
        valid_categories = ["primary", "promotions", "social", "updates", "forums"]
        keyword_search = None
        
        if category:
            category_lower = category.lower().strip()
            if category_lower in valid_categories:
                # Exclude spam, promotions, social from summaries
                if category_lower in ["promotions", "social", "spam"]:
                    # Block summary requests for promotions, social, spam
                    query = query.filter(Email.id == "none")
                else:
                    query = query.filter(Email.category == category_lower)
            else:
                # Treat as keyword search query
                keyword_search = category
        else:
            # By default exclude spam, promotions, and social
            query = query.filter(Email.category.notin_(["promotions", "social", "spam"]))
            
        if keyword_search:
            query = query.filter(
                or_(
                    Email.subject.contains(keyword_search),
                    Email.body.contains(keyword_search)
                )
            )
        
        emails = query.order_by(desc(Email.received_at)).limit(limit).all()
        
        result_list = []
        for email in emails:
            summary = email.analysis.summary if email.analysis else email.body[:200]
            result_list.append({
                "id": email.id,
                "sender": email.sender,
                "subject": email.subject,
                "category": email.category,
                "summary": summary
            })
            
        return {
            "filters": {"sender": sender, "category": category, "limit": limit},
            "count": len(result_list),
            "emails": result_list
        }

    def _tool_draft_reply(self, db: Session, email_id: str = None, sender: str = None, reply_content: str = "") -> dict:
        """Draft a reply email and save it in SuggestedAction database"""
        target_email = None
        
        if email_id:
            target_email = db.query(Email).filter_by(id=email_id).first()
        elif sender:
            target_email = db.query(Email).filter(Email.sender.contains(sender)).order_by(desc(Email.received_at)).first()
            
        if not target_email:
            # Get latest email as fallback
            target_email = db.query(Email).order_by(desc(Email.received_at)).first()
            
        if not target_email:
            return {"error": "No emails found in mailbox to reply to."}

        # Call LLM to format/write a professional reply email
        system_prompt = "You are a professional email composer. Draft a reply based on the context."
        prompt = (
            f"Original Subject: {target_email.subject}\n"
            f"Original Sender: {target_email.sender}\n"
            f"Original Body: {target_email.body}\n\n"
            f"Instructions for reply: {reply_content}\n\n"
            f"Write a professional email body. Do not include subject line or signature placeholder."
        )
        reply_body = self.llm.generate_completion(prompt, system_prompt=system_prompt)

        # Create SuggestedAction
        # Resolve decision link (create a temp decision if email doesn't have one)
        decision_id = None
        if target_email.decisions:
            decision_id = target_email.decisions[0].id
            
        action_id = f"act-reply-{str(uuid.uuid4())}"
        action = SuggestedAction(
            id=action_id,
            decision_id=decision_id,
            action_type="send_email",
            payload={
                "to": "hemanthvignesh27@gmail.com",
                "subject": f"Re: {target_email.subject or 'Smart Bee Inquiry'}",
                "body": reply_body,
                "is_ai_generated": True,
                "priority": "medium"
            },
            status="pending", # pending approval draft
            scheduled_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db.add(action)
        db.commit()

        return {
            "action_id": action_id,
            "to": "hemanthvignesh27@gmail.com",
            "subject": f"Re: {target_email.subject}",
            "body": reply_body,
            "status": "pending_approval"
        }

    def _tool_show_today_schedule(self, db: Session) -> dict:
        """Show meeting events for today"""
        # Fetch actions of type create_calendar_event
        actions = db.query(SuggestedAction).filter(
            SuggestedAction.action_type == "create_calendar_event"
        ).all()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        today_meetings = []
        for act in actions:
            payload = act.payload or {}
            meeting_date = payload.get("date")
            if meeting_date == today_str:
                today_meetings.append({
                    "id": act.id,
                    "title": payload.get("title", "Meeting"),
                    "time": payload.get("time", "TBD"),
                    "duration": payload.get("duration", "30m"),
                    "status": act.status,
                    "meet_link": act.execution_metadata.get("meet_link") if act.execution_metadata else None,
                    "event_link": act.execution_metadata.get("event_link") if act.execution_metadata else None
                })
                
        return {
            "today_date": today_str,
            "count": len(today_meetings),
            "meetings": today_meetings
        }

    def _tool_schedule_meeting(self, db: Session, recipient_email: str, title: str, date: str, time: str, agenda: str = None) -> dict:
        """Schedule calendar event (Google Meet) and auto-send invitation email"""
        # Force recipient_email to user requested value
        recipient_email = "hemanthvignesh27@gmail.com"
        # Create calendar event
        payload = {
            "title": title,
            "date": date,
            "time": time,
            "priority": "high"
        }
        
        # Call calendar executor to create event
        cal_result = create_calendar_event(payload)
        meet_link = cal_result.get("meet_link", "https://meet.google.com/mock-meet")
        event_link = cal_result.get("event_link", "#")
        
        # Save meeting action to DB
        action_id = f"act-event-{str(uuid.uuid4())}"
        meeting_action = SuggestedAction(
            id=action_id,
            decision_id=None,
            action_type="create_calendar_event",
            payload=payload,
            status="executed",
            execution_metadata={
                "event_id": cal_result.get("event_id"),
                "event_link": event_link,
                "meet_link": meet_link
            }
        )
        db.add(meeting_action)
        
        # Automatically schedule invitation email (status="scheduled", scheduled_at=now) so background daemon sends it immediately
        email_body = (
            f"Hi,\n\n"
            f"You have been scheduled for a meeting with Hemanth:\n"
            f"• Title: {title}\n"
            f"• Date: {date}\n"
            f"• Time: {time} (Asia/Kolkata)\n"
            f"• Join Google Meet: {meet_link}\n"
            f"{f'• Agenda: {agenda}' if agenda else ''}\n\n"
            f"Please click here to add to your calendar:\n{event_link}\n\n"
            f"Best regards,\nSmart Bee assistant"
        )
        
        invitation_action = SuggestedAction(
            id=f"act-email-{str(uuid.uuid4())}",
            decision_id=None,
            action_type="send_email",
            payload={
                "to": recipient_email,
                "subject": f"Invitation: {title} @ {date} {time}",
                "body": email_body,
                "is_ai_generated": True,
                "priority": "high"
            },
            status="scheduled",
            scheduled_at=datetime.utcnow() # send immediately
        )
        db.add(invitation_action)
        db.commit()

        return {
            "message": "Meeting scheduled successfully",
            "calendar_event_id": action_id,
            "recipient": recipient_email,
            "date": date,
            "time": time,
            "meet_link": meet_link,
            "event_link": event_link
        }

    def _tool_schedule_follow_up(self, db: Session, recipient_email: str, subject: str, body: str, delay_hours: float = None, scheduled_time: str = None) -> dict:
        """Schedule follow-up email"""
        # Force recipient_email to user requested value
        recipient_email = "hemanthvignesh27@gmail.com"
        if scheduled_time:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_time.replace(" ", "T"))
            except Exception as e:
                logger.warning(f"Failed to parse scheduled_time: {e}. Falling back to 24h delay.")
                scheduled_at = datetime.utcnow() + timedelta(days=1)
        elif delay_hours is not None:
            scheduled_at = datetime.utcnow() + timedelta(hours=delay_hours)
        else:
            scheduled_at = datetime.utcnow() + timedelta(days=1)
            
        action_id = f"act-email-{str(uuid.uuid4())}"
        action = SuggestedAction(
            id=action_id,
            decision_id=None,
            action_type="send_email",
            payload={
                "to": recipient_email,
                "subject": subject,
                "body": body,
                "is_ai_generated": True,
                "priority": "medium"
            },
            status="scheduled",
            scheduled_at=scheduled_at
        )
        
        db.add(action)
        db.commit()
        
        return {
            "action_id": action_id,
            "recipient": recipient_email,
            "subject": subject,
            "scheduled_time": scheduled_at.isoformat(),
            "status": "scheduled"
        }
