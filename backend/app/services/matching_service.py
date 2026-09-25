"""
Matching service — orchestrates fit scoring for a resume ↔ job pair.

Flow:
1. Load the career profile and job posting from Postgres.
2. Extract structured skills from both sides.
3. Embed job requirements + resume skills.
4. Run deterministic fit_scorer.
5. Generate LLM explanation citing matched/missing evidence.
6. Cache the MatchResult in Postgres.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.fit_scorer import FitScoreResult, score_fit
from app.core.skill_extractor import extract_skills
from app.integrations import embedding_client
from app.integrations.llm_client import generate_text
from app.models.job_models import JobPosting, MatchResult
from app.models.profile_models import CareerProfile

logger = logging.getLogger(__name__)

_EXPLAIN_PROMPT = """
You are a career advisor. Write a clear, honest explanation of how well the candidate
fits the job based on the scoring data below. Be specific — cite which matched
requirements were satisfied and how, and which are missing.

Job: {job_title} at {company}

Matched requirements (with evidence):
{matched}

Missing requirements:
{missing}

Fit score: {score:.0%}

Write 3-5 sentences. Be direct and constructive. Do NOT invent skills not listed above.
"""


async def get_or_compute_match(
    db: AsyncSession,
    user_id: str,
    job_id: str,
) -> MatchResult:
    """
    Return cached MatchResult if available, otherwise compute and cache it.
    """
    # Check cache
    result = await db.execute(
        select(MatchResult).where(
            MatchResult.user_id == uuid.UUID(user_id),
            MatchResult.job_id == uuid.UUID(job_id),
        )
    )
    cached = result.scalar_one_or_none()
    if cached is not None:
        return cached

    return await compute_match(db, user_id, job_id)


async def compute_match(
    db: AsyncSession,
    user_id: str,
    job_id: str,
) -> MatchResult:
    """Force-recompute and cache a match result."""
    # Load profile
    profile_result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == uuid.UUID(user_id))
    )
    profile: Optional[CareerProfile] = profile_result.scalar_one_or_none()
    if profile is None:
        raise ValueError(f"No career profile found for user {user_id}")

    # Load job
    job_result = await db.execute(
        select(JobPosting).where(JobPosting.id == uuid.UUID(job_id))
    )
    job: Optional[JobPosting] = job_result.scalar_one_or_none()
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    # Extract skills
    resume_skills = [s["name"] for s in (profile.skills or []) if isinstance(s, dict)]
    if not resume_skills:
        resume_skills = await extract_skills(profile.resume_raw_text or "")

    job_requirements: list[str] = job.requirements or []
    if not job_requirements:
        job_requirements = await extract_skills(job.full_description)

    # Embed both sides
    req_embeddings = await embedding_client.embed_texts(job_requirements)
    skill_embeddings = await embedding_client.embed_texts(resume_skills)

    # Score
    score_result: FitScoreResult = score_fit(
        job_requirements=job_requirements,
        resume_skills=resume_skills,
        job_requirement_embeddings=req_embeddings,
        resume_skill_embeddings=skill_embeddings,
    )

    # LLM explanation
    matched_str = "\n".join(
        f"- {m.requirement} → matched via {m.matched_via} (evidence: {m.evidence})"
        for m in score_result.matched_requirements
    )
    missing_str = "\n".join(f"- {r}" for r in score_result.missing_requirements)

    explanation = await generate_text(
        _EXPLAIN_PROMPT.format(
            job_title=job.title,
            company=job.company,
            matched=matched_str or "None",
            missing=missing_str or "None",
            score=score_result.fit_score,
        )
    )

    # Cache in Postgres
    match_result = MatchResult(
        user_id=uuid.UUID(user_id),
        job_id=uuid.UUID(job_id),
        fit_score=score_result.fit_score,
        matched_requirements=[
            {
                "requirement": m.requirement,
                "matched_via": m.matched_via,
                "evidence": m.evidence,
            }
            for m in score_result.matched_requirements
        ],
        missing_requirements=score_result.missing_requirements,
        explanation=explanation,
    )
    db.add(match_result)
    await db.flush()

    logger.info(
        "Computed match for user=%s job=%s score=%.2f",
        user_id,
        job_id,
        score_result.fit_score,
    )
    return match_result
