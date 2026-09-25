"""Tests for core fit scorer logic."""
from __future__ import annotations

import pytest
from app.core.fit_scorer import score_fit, EMBEDDING_MATCH_THRESHOLD


def make_unit_vec(dim: int, idx: int) -> list:
    """One-hot vector of length `dim` at position `idx`."""
    v = [0.0] * dim
    v[idx] = 1.0
    return v


def test_exact_match():
    result = score_fit(
        job_requirements=["Python", "Docker"],
        resume_skills=["Python", "Docker", "SQL"],
        job_requirement_embeddings=[],
        resume_skill_embeddings=[],
    )
    assert result.fit_score == 1.0
    assert len(result.matched_requirements) == 2
    assert len(result.missing_requirements) == 0
    assert all(m.matched_via == "exact" for m in result.matched_requirements)


def test_partial_match():
    result = score_fit(
        job_requirements=["Python", "Kubernetes", "Rust"],
        resume_skills=["Python"],
        job_requirement_embeddings=[],
        resume_skill_embeddings=[],
    )
    assert 0.0 < result.fit_score < 1.0
    assert len(result.missing_requirements) == 2


def test_no_requirements_returns_full_score():
    result = score_fit(
        job_requirements=[],
        resume_skills=["Python"],
        job_requirement_embeddings=[],
        resume_skill_embeddings=[],
    )
    assert result.fit_score == 1.0


def test_no_skills_returns_zero():
    result = score_fit(
        job_requirements=["Python", "Docker"],
        resume_skills=[],
        job_requirement_embeddings=[make_unit_vec(4, 0), make_unit_vec(4, 1)],
        resume_skill_embeddings=[],
    )
    assert result.fit_score == 0.0
    assert len(result.missing_requirements) == 2


def test_embedding_fallback_match():
    """GPU-accelerated computing ↔ CUDA via embedding similarity."""
    req_emb = [make_unit_vec(4, 0)]  # "CUDA" embedding
    skill_emb = [make_unit_vec(4, 0)]  # identical — perfect cosine similarity

    result = score_fit(
        job_requirements=["GPU-accelerated computing"],
        resume_skills=["CUDA"],
        job_requirement_embeddings=req_emb,
        resume_skill_embeddings=skill_emb,
    )
    assert result.fit_score == 1.0
    assert result.matched_requirements[0].matched_via == "embedding"


def test_embedding_fallback_no_match_below_threshold():
    req_emb = [make_unit_vec(4, 0)]
    skill_emb = [make_unit_vec(4, 3)]  # orthogonal — cosine sim = 0

    result = score_fit(
        job_requirements=["Kubernetes"],
        resume_skills=["CSS"],
        job_requirement_embeddings=req_emb,
        resume_skill_embeddings=skill_emb,
    )
    assert result.fit_score == 0.0
    assert "Kubernetes" in result.missing_requirements


def test_substring_match():
    result = score_fit(
        job_requirements=["Python 3.x"],
        resume_skills=["Python"],
        job_requirement_embeddings=[],
        resume_skill_embeddings=[],
    )
    assert result.fit_score == 1.0
    assert result.matched_requirements[0].matched_via == "exact"
