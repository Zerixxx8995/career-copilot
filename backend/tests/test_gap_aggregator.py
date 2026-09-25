"""Tests for gap aggregator."""
from __future__ import annotations

from app.core.gap_aggregator import aggregate_gaps


def test_basic_aggregation():
    job_ids = ["job1", "job2", "job3"]
    missing = [
        ["Python", "Docker"],
        ["Python", "Kubernetes"],
        ["Python", "Docker", "Rust"],
    ]
    gaps = aggregate_gaps(job_ids, missing)
    # Python appears in all 3
    assert gaps[0].skill.lower() == "python"
    assert gaps[0].frequency == 3
    # Docker appears in 2
    docker_gap = next(g for g in gaps if g.skill.lower() == "docker")
    assert docker_gap.frequency == 2


def test_empty_inputs():
    gaps = aggregate_gaps([], [])
    assert gaps == []


def test_no_gaps():
    gaps = aggregate_gaps(["job1"], [[]])
    assert gaps == []


def test_sample_job_ids_capped_at_three():
    job_ids = [f"job{i}" for i in range(10)]
    missing = [["Python"] for _ in range(10)]
    gaps = aggregate_gaps(job_ids, missing)
    assert gaps[0].frequency == 10
    assert len(gaps[0].sample_job_ids) <= 3


def test_sorted_descending():
    job_ids = ["j1", "j2", "j3"]
    missing = [
        ["Docker"],
        ["Docker", "Rust"],
        ["Docker", "Rust", "Go"],
    ]
    gaps = aggregate_gaps(job_ids, missing)
    freqs = [g.frequency for g in gaps]
    assert freqs == sorted(freqs, reverse=True)
