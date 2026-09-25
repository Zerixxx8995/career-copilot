"""
save_feedback tool — thin wrapper over feedback_service.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.feedback_service import save_feedback as _save


async def save_feedback(
    db: AsyncSession,
    user_id: str,
    job_id: str,
    action: str,
) -> Dict[str, Any]:
    """
    Record user feedback on a job and update preference weights.

    Input:  { job_id: string, action: "interested"|"not_interested"|"applied" }
    Output: { status: "ok", updated_preference_weights: {...} }
    """
    return await _save(db, user_id, job_id, action)
