"""
Fit scorer — deterministic structured matching with embedding fallback.

Architecture:
1. Normalise both skill lists to lowercase.
2. Try exact string match — O(n).
3. For unmatched requirements, try fuzzy substring match.
4. For still-unmatched, fall back to cosine similarity of embeddings.
5. LLM is NOT called here — it's called in matching_service.py to write
   the natural-language explanation citing which method matched what.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Literal, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MatchMethod = Literal["exact", "fuzzy", "embedding", "none"]
EMBEDDING_MATCH_THRESHOLD = 0.75  # cosine similarity cutoff


@dataclass
class RequirementMatch:
    requirement: str
    matched: bool
    matched_via: MatchMethod
    evidence: str  # the resume skill/phrase that matched


@dataclass
class FitScoreResult:
    fit_score: float  # 0.0 – 1.0
    matched_requirements: List[RequirementMatch]
    missing_requirements: List[str]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _normalise(s: str) -> str:
    return s.lower().strip()


def _exact_match(requirement: str, resume_skills: List[str]) -> Tuple[bool, str]:
    req_norm = _normalise(requirement)
    for skill in resume_skills:
        if req_norm == _normalise(skill):
            return True, skill
        # substring match (e.g. requirement="Python 3.x", skill="Python")
        if req_norm in _normalise(skill) or _normalise(skill) in req_norm:
            return True, skill
    return False, ""


def score_fit(
    job_requirements: List[str],
    resume_skills: List[str],
    job_requirement_embeddings: List[List[float]],
    resume_skill_embeddings: List[List[float]],
) -> FitScoreResult:
    """
    Score how well the resume skills satisfy the job requirements.

    Parameters
    ----------
    job_requirements : List[str]
        Plain-text requirement strings from the job posting.
    resume_skills : List[str]
        Plain-text skill strings from the candidate's profile.
    job_requirement_embeddings : List[List[float]]
        One embedding vector per job requirement (same order).
    resume_skill_embeddings : List[List[float]]
        One embedding vector per resume skill (same order).
    """
    if not job_requirements:
        return FitScoreResult(
            fit_score=1.0,
            matched_requirements=[],
            missing_requirements=[],
        )

    matched: List[RequirementMatch] = []
    missing: List[str] = []

    for idx, req in enumerate(job_requirements):
        # Step 1 — exact / fuzzy match
        found, evidence = _exact_match(req, resume_skills)
        if found:
            matched.append(
                RequirementMatch(
                    requirement=req,
                    matched=True,
                    matched_via="exact",
                    evidence=evidence,
                )
            )
            continue

        # Step 2 — embedding fallback
        if job_requirement_embeddings and resume_skill_embeddings:
            req_emb = job_requirement_embeddings[idx]
            best_sim = 0.0
            best_skill = ""
            for sidx, skill_emb in enumerate(resume_skill_embeddings):
                sim = _cosine_similarity(req_emb, skill_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_skill = resume_skills[sidx] if sidx < len(resume_skills) else ""

            if best_sim >= EMBEDDING_MATCH_THRESHOLD:
                matched.append(
                    RequirementMatch(
                        requirement=req,
                        matched=True,
                        matched_via="embedding",
                        evidence=f"{best_skill} (similarity={best_sim:.2f})",
                    )
                )
                continue

        missing.append(req)

    total = len(job_requirements)
    score = len(matched) / total if total > 0 else 0.0

    logger.debug(
        "Fit score: %.2f (%d/%d requirements matched)", score, len(matched), total
    )

    return FitScoreResult(
        fit_score=round(score, 3),
        matched_requirements=matched,
        missing_requirements=missing,
    )
