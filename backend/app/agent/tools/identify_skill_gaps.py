"""
identify_skill_gaps tool — aggregates missing requirements across multiple jobs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gap_aggregator import aggregate_gaps
from app.integrations.llm_client import generate_text
from app.services.matching_service import get_or_compute_match

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = """
You are a career advisor. Below are the top recurring skill gaps a candidate has
across multiple job postings they're targeting. Write a concise, actionable summary
(3-5 sentences) that:
1. Identifies the most critical gaps to address first
2. Suggests how to close them (courses, projects, or certifications)
3. Is encouraging and constructive

Skill gaps (sorted by frequency):
{gaps}

Summary:
"""


async def identify_skill_gaps(
    db: AsyncSession,
    user_id: str,
    job_ids: List[str],
) -> Dict[str, Any]:
    """
    Identify recurring skill gaps across a list of job IDs.

    Input:  { job_ids: string[] }
    Output: {
      recurring_gaps: [{ skill, frequency, sample_job_ids }],
      summary: string
    }
    """
    missing_per_job: List[List[str]] = []

    for job_id in job_ids:
        try:
            match = await get_or_compute_match(db, user_id, job_id)
            missing_per_job.append(match.missing_requirements or [])
        except Exception as exc:
            logger.warning("Could not match job %s: %s", job_id, exc)
            missing_per_job.append([])

    gaps = aggregate_gaps(job_ids, missing_per_job)

    # LLM summary of gaps
    if gaps:
        gaps_text = "\n".join(
            f"- {g.skill}: missing in {g.frequency} job(s)" for g in gaps[:10]
        )
        summary = await generate_text(_SUMMARY_PROMPT.format(gaps=gaps_text))
    else:
        summary = "No significant recurring skill gaps found — your profile covers the key requirements well!"

    return {
        "recurring_gaps": [
            {
                "skill": g.skill,
                "frequency": g.frequency,
                "sample_job_ids": g.sample_job_ids,
            }
            for g in gaps
        ],
        "summary": summary,
    }
