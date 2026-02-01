"""Tests for GitHub Actions export."""

from suite.comparison import BehaviorComparison, ComparisonResult, ComparisonVerdict
from suite.export.github import generate_github_summary, print_github_annotations


def test_github_export_summary():
    result = ComparisonResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        comparability_key="suite-test:1.0.0",
        verdict=ComparisonVerdict.PASS,
        headline_baseline=80.0,
        headline_current=82.0,
        headline_delta_pct=2.5,
        behavior_comparisons=[
            BehaviorComparison(
                behavior_id="BHV-1",
                name="Behavior One",
                baseline_score=80.0,
                current_score=82.0,
                delta=2.0,
                delta_pct=2.5,
                threshold_pct=5.0,
                min_score=None,
                verdict=ComparisonVerdict.PASS,
                message="within thresholds",
            )
        ],
        baseline_halts=0,
        current_halts=0,
        new_halts=[],
        regressions=0,
        warnings=0,
        passes=1,
        exit_code=0,
        ci_message="PASS",
    )

    summary = generate_github_summary(result)
    assert "Janus Labs Benchmark Comparison" in summary
    assert "| BHV-1 |" in summary


def test_github_export_annotations(capsys):
    result = ComparisonResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        comparability_key="suite-test:1.0.0",
        verdict=ComparisonVerdict.REGRESSION,
        headline_baseline=80.0,
        headline_current=70.0,
        headline_delta_pct=-12.5,
        behavior_comparisons=[
            BehaviorComparison(
                behavior_id="BHV-1",
                name="Behavior One",
                baseline_score=80.0,
                current_score=70.0,
                delta=-10.0,
                delta_pct=-12.5,
                threshold_pct=5.0,
                min_score=None,
                verdict=ComparisonVerdict.REGRESSION,
                message="drop exceeds threshold",
            )
        ],
        baseline_halts=0,
        current_halts=0,
        new_halts=[],
        regressions=1,
        warnings=0,
        passes=0,
        exit_code=1,
        ci_message="REGRESSION",
    )

    print_github_annotations(result)
    output = capsys.readouterr().out
    assert "::error" in output
