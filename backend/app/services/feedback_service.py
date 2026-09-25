"""
Feedback service — writes FeedbackEvent and updates CareerProfile preference weights.

Weight update rules:
- "interested"     → +0.2 for job's role_category
- "applied"        → +0.3 for job's role_category
- "not_interested" → -0.2 for job's role_category
Weights are clamped to [-1.0, 1.0].
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.feedback_models import FeedbackEvent
from app.models.job_models import JobPosting
from app.models.profile_models import CareerProfile

logger = logging.getLogger(__name__)

_WEIGHT_DELTA = {
    "interested": 0.2,
    "applied": 0.3,
    "not_interested": -0.2,
}


async def save_feedback(
    db: AsyncSession,
    user_id: str,
    job_id: str,
    action: str,
) -> dict:
    """
    Record a feedback event and update the user's preference weights.
    Returns updated preference_weights.
    """
    if action not in _WEIGHT_DELTA:
        raise ValueError(f"Invalid action '{action}'. Must be one of {list(_WEIGHT_DELTA)}")

    # Write feedback event
    event = FeedbackEvent(
        user_id=uuid.UUID(user_id),
        job_id=uuid.UUID(job_id),
        action=action,
    )
    db.add(event)

    # Load job to get role_category
    job_result = await db.execute(
        select(JobPosting).where(JobPosting.id == uuid.UUID(job_id))
    )
    job = job_result.scalar_one_or_none()
    category = job.role_category.lower() if job else "general"

    # Load profile and update weights
    profile_result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == uuid.UUID(user_id))
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        profile = CareerProfile(user_id=uuid.UUID(user_id))
        db.add(profile)

    weights: dict = dict(profile.preference_weights or {})
    delta = _WEIGHT_DELTA[action]
    current = weights.get(category, 0.0)
    weights[category] = max(-1.0, min(1.0, current + delta))
    profile.preference_weights = weights

    await db.flush()

    logger.info(
        "Feedback saved: user=%s job=%s action=%s category=%s new_weight=%.2f",
        user_id, job_id, action, category, weights[category],
    )

    return {"status": "ok", "updated_preference_weights": weights}
