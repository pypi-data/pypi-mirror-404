"""Tests for comparison logic."""

from suite.comparison import ComparisonVerdict, compare_results
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult
from suite.thresholds import BehaviorThreshold, ThresholdConfig


def _suite_result(score: float, halted: bool = False) -> SuiteResult:
    return SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=score,
        grade="A",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=score,
                trust_elasticity=score,
                grade="A",
                passed=True,
                halted=halted,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=halted,
            halted_count=1 if halted else 0,
            halted_behaviors=["BHV-1"] if halted else [],
            foundation_check_rate=0.1,
        ),
        comparability_key="suite-test:1.0.0",
        total_rollouts=10,
        total_duration_ms=1000,
    )


def test_compare_regression_and_warning():
    baseline = _suite_result(80.0)
    current = _suite_result(70.0)
    config = ThresholdConfig(
        suite_id="suite-test",
        behaviors={
            "BHV-1": BehaviorThreshold(
                behavior_id="BHV-1",
                max_regression_pct=5.0,
                min_score=75.0,
                required=True,
            )
        },
    )

    result = compare_results(baseline, current, config)
    assert result.verdict == ComparisonVerdict.REGRESSION
    assert result.exit_code == 1

    config.behaviors["BHV-1"].required = False
    result = compare_results(baseline, current, config)
    assert result.verdict == ComparisonVerdict.WARNING


def test_compare_detects_new_halts():
    baseline = _suite_result(80.0, halted=False)
    current = _suite_result(80.0, halted=True)
    config = ThresholdConfig(
        suite_id="suite-test",
        fail_on_any_halt=True,
    )

    result = compare_results(baseline, current, config)
    assert result.new_halts == ["BHV-1"]
    assert result.verdict == ComparisonVerdict.REGRESSION


def test_compare_mismatch():
    baseline = _suite_result(80.0)
    current = _suite_result(80.0)
    current.comparability_key = "other:1.0.0"
    config = ThresholdConfig(suite_id="suite-test")

    result = compare_results(baseline, current, config)
    assert result.verdict == ComparisonVerdict.ERROR
    assert result.exit_code == 2
