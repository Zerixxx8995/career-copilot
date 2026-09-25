"""
Feedback controller — validates and routes feedback events.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.services.feedback_service import save_feedback
from sqlalchemy.ext.asyncio import AsyncSession

VALID_ACTIONS = {"interested", "not_interested", "applied"}


class FeedbackRequest(BaseModel):
    job_id: str = Field(..., description="UUID of the job being rated")
    action: str = Field(..., description="One of: interested, not_interested, applied")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in VALID_ACTIONS:
            raise ValueError(f"action must be one of {VALID_ACTIONS}")
        return v


async def handle_feedback(
    db: AsyncSession,
    user_id: str,
    request: FeedbackRequest,
) -> dict:
    return await save_feedback(
        db=db,
        user_id=user_id,
        job_id=request.job_id,
        action=request.action,
    )
