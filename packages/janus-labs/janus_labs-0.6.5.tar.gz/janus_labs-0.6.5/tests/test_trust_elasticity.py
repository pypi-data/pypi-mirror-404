"""Tests for TrustElasticityMetric."""

from deepeval.test_case import LLMTestCase

from gauge.trust_elasticity import TrustElasticityMetric


def test_trust_elasticity_basic():
    """TrustElasticityMetric calculates valid score."""
    metric = TrustElasticityMetric(base_score=8.0)
    test_case = LLMTestCase(input="test", actual_output="output")

    score = metric.measure(test_case)

    assert 0.0 <= score <= 1.0
    assert metric.is_successful()


def test_trust_elasticity_with_halt():
    """Halted runs receive penalty."""
    bundle = {
        "transcript": [],
        "tool_traces": [],
        "repo_diff": {},
        "test_results": {},
        "timings": {},
        "exit_code": "halt",
    }

    metric = TrustElasticityMetric(base_score=8.0, bundle=bundle)
    test_case = LLMTestCase(input="test", actual_output="output")

    score = metric.measure(test_case)

    assert score < 0.8


def test_score_to_grade():
    """Grade thresholds are correct."""
    assert TrustElasticityMetric.score_to_grade(95) == "S"
    assert TrustElasticityMetric.score_to_grade(85) == "A"
    assert TrustElasticityMetric.score_to_grade(75) == "B"
    assert TrustElasticityMetric.score_to_grade(65) == "C"
    assert TrustElasticityMetric.score_to_grade(55) == "D"
    assert TrustElasticityMetric.score_to_grade(45) == "F"
