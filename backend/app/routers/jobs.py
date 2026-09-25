"""Jobs router — URL mapping only."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.jobs_controller import handle_get_job, handle_list_jobs
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", summary="List and filter job postings")
async def list_jobs(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_list_jobs(db=db, user_id=user_id, role=role, location=location, limit=limit)


@router.get("/{job_id}", summary="Get full job posting details")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_get_job(db=db, user_id=user_id, job_id=job_id)


@router.get("/{job_id}/match", summary="Get fit score for authenticated user vs job")
async def match_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    from app.services.matching_service import get_or_compute_match
    result = await get_or_compute_match(db=db, user_id=user_id, job_id=job_id)
    return {
        "job_id": str(result.job_id),
        "fit_score": result.fit_score,
        "matched_requirements": result.matched_requirements,
        "missing_requirements": result.missing_requirements,
        "explanation": result.explanation,
    }
