"""
Ranking service — re-ranks job search results using the user's stored preference weights.

The re-ranking formula:
  final_score = base_relevance + (preference_weight_for_category * PREF_SCALE)

PREF_SCALE controls how strongly feedback shifts ranking vs. keyword relevance.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

PREF_SCALE = 0.3  # max preference adjustment added to base relevance


def rerank_jobs(
    jobs: List[Dict[str, Any]],
    preference_weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Re-rank a list of job dicts using preference weights.

    Each job dict must have at least:
      - "role_category": str
      - "relevance": float  (0.0–1.0, set by the caller)

    Returns the list sorted descending by adjusted_score, with
    "adjusted_score" added to each dict.
    """
    for job in jobs:
        category = (job.get("role_category") or "").lower()
        weight = preference_weights.get(category, 0.0)
        base = job.get("relevance", 0.5)
        job["adjusted_score"] = round(base + weight * PREF_SCALE, 4)

    ranked = sorted(jobs, key=lambda j: j["adjusted_score"], reverse=True)
    logger.debug("Re-ranked %d jobs using preference weights", len(ranked))
    return ranked
