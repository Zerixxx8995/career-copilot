"""
Jobs controller — list/filter jobs and get job details.
"""
from __future__ import annotations

from typing import Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job_models import JobPosting


async def handle_list_jobs(
    db: AsyncSession,
    user_id: str,
    role: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
) -> dict:
    stmt = select(JobPosting)
    all_jobs = (await db.execute(stmt)).scalars().all()

    results = []
    for job in all_jobs:
        if role and role.lower() not in (job.title + job.role_category).lower():
            continue
        if location and location.lower() not in job.location.lower():
            continue
        results.append({
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "role_category": job.role_category,
            "short_description": job.full_description[:200] + "…",
        })

    return {"jobs": results[:limit], "total": len(results)}


async def handle_get_job(
    db: AsyncSession,
    user_id: str,
    job_id: str,
) -> dict:
    result = await db.execute(
        select(JobPosting).where(JobPosting.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return {
        "job_id": str(job.id),
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "role_category": job.role_category,
        "full_description": job.full_description,
        "requirements": job.requirements,
        "source": job.source,
        "created_at": job.created_at.isoformat(),
    }
