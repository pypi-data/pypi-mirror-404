"""Tests for BenchmarkReport generation."""

import pytest

from forge.behavior import BehaviorSpec
from gauge.report import generate_benchmark_report


def test_generate_benchmark_report():
    """BenchmarkReport generation produces valid output."""
    behavior = BehaviorSpec(
        behavior_id="BHV-TEST",
        name="Test",
        description="Test behavior",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    report = generate_benchmark_report(
        behaviors=[behavior],
        behavior_scores={"BHV-TEST": [0.8, 0.7, 0.9]},
        trust_elasticity_scores={"BHV-TEST": [80.0, 70.0, 90.0]},
        config_fingerprint="abc123",
        duration_ms=5000,
    )

    assert report["report_id"] is not None
    assert len(report["behaviors"]) == 1
    assert report["behaviors"][0]["mean_score"] == pytest.approx(0.8, rel=0.01)
    assert report["aggregate_metrics"]["trust_elasticity"] == pytest.approx(80.0, rel=0.01)
    assert report["aggregate_metrics"]["grade"] == "A"
