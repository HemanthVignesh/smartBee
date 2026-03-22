"""Models package - Import all models here"""

from app.models.email import Email
from app.models.analysis import EmailAnalysis
from app.models.decision import Decision
from app.models.action import SuggestedAction
from app.models.feedback import UserFeedback

__all__ = [
    'Email',
    'EmailAnalysis',
    'Decision',
    'SuggestedAction',
    'UserFeedback'
]