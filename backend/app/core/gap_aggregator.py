"""
Gap aggregator — counts recurring missing requirements across multiple match results.
Pure aggregation logic; no LLM, no HTTP, no DB access.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List


@dataclass
class SkillGap:
    skill: str
    frequency: int
    sample_job_ids: List[str]


def aggregate_gaps(
    job_ids: List[str],
    missing_requirements_per_job: List[List[str]],
) -> List[SkillGap]:
    """
    Aggregate missing requirements across multiple jobs into a ranked gap list.

    Parameters
    ----------
    job_ids : List[str]
        Job IDs in the same order as missing_requirements_per_job.
    missing_requirements_per_job : List[List[str]]
        Missing requirement strings for each job (same order as job_ids).

    Returns
    -------
    List[SkillGap]
        Sorted descending by frequency.
    """
    freq: Counter[str] = Counter()
    gap_to_jobs: dict[str, List[str]] = {}

    for job_id, missing in zip(job_ids, missing_requirements_per_job):
        for req in missing:
            key = req.strip().lower()
            freq[key] += 1
            gap_to_jobs.setdefault(key, [])
            if job_id not in gap_to_jobs[key]:
                gap_to_jobs[key].append(job_id)

    results: List[SkillGap] = []
    for skill_key, count in freq.most_common():
        # Use original casing from first occurrence
        results.append(
            SkillGap(
                skill=skill_key.title(),
                frequency=count,
                sample_job_ids=gap_to_jobs[skill_key][:3],  # cap for readability
            )
        )

    return results
