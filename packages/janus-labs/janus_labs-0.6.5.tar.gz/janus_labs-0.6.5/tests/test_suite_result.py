"""Tests for SuiteResult generation."""

import pytest

from forge.behavior import BehaviorSpec
from gauge.report import generate_benchmark_report
from suite.definition import BenchmarkSuite
from suite.result import generate_suite_result


def test_generate_suite_result_headline_score():
    behavior = BehaviorSpec(
        behavior_id="BHV-TEST",
        name="Behavior Test",
        description="Test",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )
    suite = BenchmarkSuite(
        suite_id="suite-test",
        version="1.0.0",
        display_name="Suite Test",
        description="Suite test",
        behaviors=[behavior],
    )

    report = generate_benchmark_report(
        behaviors=[behavior],
        behavior_scores={"BHV-TEST": [0.8, 0.7, 0.9]},
        trust_elasticity_scores={"BHV-TEST": [80.0, 70.0, 90.0]},
        config_fingerprint="abc123",
    )

    suite_result = generate_suite_result(
        suite=suite,
        behavior_results={"BHV-TEST": report},
        config_fingerprint="abc123",
        duration_ms=5000,
    )

    assert suite_result.headline_score == pytest.approx(80.0, rel=0.01)
    assert suite_result.grade == "A"
    assert suite_result.comparability_key == "suite-test:1.0.0"
