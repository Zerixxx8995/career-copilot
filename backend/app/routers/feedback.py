"""Feedback router — URL mapping only."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.feedback_controller import FeedbackRequest, handle_feedback
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("", summary="Record user feedback on a job posting")
async def post_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_feedback(db=db, user_id=user_id, request=request)
