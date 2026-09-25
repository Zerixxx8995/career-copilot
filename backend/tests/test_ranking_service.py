"""Tests for ranking service."""
from __future__ import annotations

from app.services.ranking_service import rerank_jobs, PREF_SCALE


def make_job(job_id: str, category: str, relevance: float = 0.5) -> dict:
    return {"job_id": job_id, "role_category": category, "relevance": relevance}


def test_positive_weight_raises_score():
    jobs = [make_job("j1", "ml", 0.5), make_job("j2", "backend", 0.5)]
    weights = {"ml": 1.0}
    ranked = rerank_jobs(jobs, weights)
    assert ranked[0]["job_id"] == "j1"
    assert ranked[0]["adjusted_score"] > 0.5


def test_negative_weight_lowers_score():
    jobs = [make_job("j1", "frontend", 0.8), make_job("j2", "ml", 0.6)]
    weights = {"frontend": -1.0, "ml": 0.5}
    ranked = rerank_jobs(jobs, weights)
    assert ranked[0]["job_id"] == "j2"


def test_no_weights_preserves_relevance_order():
    jobs = [make_job("j1", "ml", 0.9), make_job("j2", "ml", 0.4)]
    ranked = rerank_jobs(jobs, {})
    assert ranked[0]["job_id"] == "j1"


def test_adjusted_score_clamped_correctly():
    jobs = [make_job("j1", "ml", 0.5)]
    weights = {"ml": 1.0}
    ranked = rerank_jobs(jobs, weights)
    assert ranked[0]["adjusted_score"] == round(0.5 + 1.0 * PREF_SCALE, 4)


def test_empty_jobs():
    assert rerank_jobs([], {"ml": 1.0}) == []
