"""
match_resume_to_job tool — thin wrapper over matching_service.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.matching_service import get_or_compute_match


async def match_resume_to_job(
    db: AsyncSession,
    user_id: str,
    job_id: str,
) -> Dict[str, Any]:
    """
    Score how well the user's resume matches a specific job.

    Input:  { job_id: string }
    Output: {
      job_id, fit_score, matched_requirements, missing_requirements, explanation
    }
    """
    result = await get_or_compute_match(db, user_id, job_id)

    return {
        "job_id": job_id,
        "fit_score": result.fit_score,
        "matched_requirements": result.matched_requirements,
        "missing_requirements": result.missing_requirements,
        "explanation": result.explanation,
    }
