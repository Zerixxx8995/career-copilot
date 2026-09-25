"""
search_jobs tool — queries the static job store with keyword + location filtering,
then re-ranks results using the user's stored preference weights.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job_models import JobPosting
from app.models.profile_models import CareerProfile
from app.services.ranking_service import rerank_jobs

logger = logging.getLogger(__name__)


async def search_jobs(
    db: AsyncSession,
    user_id: str,
    role_keywords: List[str],
    location: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Search jobs by keyword and optional location, re-ranked by user preferences.

    Input schema  (matches tool_registry.py definition):
      role_keywords: string[]   — e.g. ["ML Engineer", "Machine Learning"]
      location: string?         — e.g. "Mumbai"
      limit: int?               — default 10

    Output schema:
      { jobs: [{ job_id, title, company, location, role_category, short_description, relevance, adjusted_score }] }
    """
    stmt = select(JobPosting)

    all_jobs = (await db.execute(stmt)).scalars().all()

    # Filter by keywords (title or description match)
    keywords_lower = [k.lower() for k in role_keywords]
    filtered = []
    for job in all_jobs:
        searchable = (job.title + " " + job.full_description + " " + job.role_category).lower()
        matched_keywords = sum(1 for kw in keywords_lower if kw in searchable)
        if matched_keywords == 0:
            continue
        relevance = min(1.0, matched_keywords / max(len(keywords_lower), 1))

        if location and location.lower() not in job.location.lower():
            relevance *= 0.5  # penalise location mismatch but don't exclude

        filtered.append({
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "role_category": job.role_category,
            "short_description": job.full_description[:200] + "…",
            "relevance": relevance,
        })

    # Load preference weights for re-ranking
    profile_result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == uuid.UUID(user_id))
    )
    profile = profile_result.scalar_one_or_none()
    weights = profile.preference_weights if profile else {}

    ranked = rerank_jobs(filtered, weights)
    return {"jobs": ranked[:limit]}
