"""Tests for enhanced CLI compare command."""

from cli.main import cmd_compare
from suite.export.json_export import export_json
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult


def _suite_result(score: float, key: str) -> SuiteResult:
    return SuiteResult(
        suite_id="refactor-storm",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=score,
        grade="A",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-001-test-cheating",
                name="Behavior One",
                score=score,
                trust_elasticity=score,
                grade="A",
                passed=True,
                halted=False,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=False,
            halted_count=0,
            halted_behaviors=[],
            foundation_check_rate=0.1,
        ),
        comparability_key=key,
        total_rollouts=10,
        total_duration_ms=1000,
    )


def test_cli_compare_with_config(tmp_path, capsys):
    baseline = _suite_result(90.0, "refactor-storm:1.0.0")
    current = _suite_result(80.0, "refactor-storm:1.0.0")

    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    export_json(baseline, str(baseline_path))
    export_json(current, str(current_path))

    config_path = tmp_path / "thresholds.yaml"
    config_path.write_text(
        "\n".join(
            [
                "suite_id: refactor-storm",
                "default_max_regression_pct: 5.0",
                "behaviors:",
                "  BHV-001-test-cheating:",
                "    max_regression_pct: 3.0",
                "    required: true",
            ]
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "comparison.json"

    class Args:
        baseline = str(baseline_path)
        current = str(current_path)
        config = str(config_path)
        output = str(output_path)
        format = "text"
        threshold = 5.0

    exit_code = cmd_compare(Args())
    assert exit_code == 1
    assert output_path.exists()
    captured = capsys.readouterr()
    assert "REGRESSION" in captured.out
