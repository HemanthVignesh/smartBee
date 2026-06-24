"""Main API Router - Combines all v1 endpoints"""

from fastapi import APIRouter
from app.api.v1 import emails, insights, actions, chatbot, analytics, bootstrap, settings_api, scheduled_emails

router = APIRouter()

# Include all sub-routers
router.include_router(emails.router)
router.include_router(insights.router)
router.include_router(actions.router)
router.include_router(chatbot.router)
router.include_router(analytics.router)
router.include_router(bootstrap.router)
router.include_router(settings_api.router)
router.include_router(scheduled_emails.router)