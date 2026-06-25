"""Models package - Import all models here"""

from app.models.email import Email
from app.models.analysis import EmailAnalysis
from app.models.decision import Decision
from app.models.action import SuggestedAction
from app.models.feedback import UserFeedback
from app.models.user import User
from app.models.audit import AuditLog
from app.models.chat_history import ChatHistory

__all__ = [
    'Email',
    'EmailAnalysis',
    'Decision',
    'SuggestedAction',
    'UserFeedback',
    'User',
    'AuditLog',
    'ChatHistory'
]