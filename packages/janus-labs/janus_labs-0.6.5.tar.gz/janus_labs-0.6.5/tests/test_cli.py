"""Tests for CLI commands."""

from cli.main import cmd_compare, cmd_export, cmd_run
from suite.export.json_export import export_json
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult


def test_cli_run(tmp_path, capsys):
    class Args:
        suite = "refactor-storm"
        output = str(tmp_path / "suite.json")
        format = "json"
        judge = False  # Don't use local LLM
        mock = True  # Use mock mode for fast testing (JL-174.5)
        model = "gpt-4o"  # Default, unused in mock mode

    exit_code = cmd_run(Args())
    assert exit_code == 0
    assert (tmp_path / "suite.json").exists()
    captured = capsys.readouterr()
    assert "Suite refactor-storm complete" in captured.out


def test_cli_compare(tmp_path):
    baseline = SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=90.0,
        grade="S",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=90.0,
                trust_elasticity=90.0,
                grade="S",
                passed=True,
                halted=False,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=False,
            halted_count=0,
            halted_behaviors=[],
            foundation_check_rate=0.0,
        ),
        comparability_key="suite-test:1.0.0",
        total_rollouts=0,
        total_duration_ms=0,
    )
    current = SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=80.0,
        grade="A",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=80.0,
                trust_elasticity=80.0,
                grade="A",
                passed=True,
                halted=False,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=False,
            halted_count=0,
            halted_behaviors=[],
            foundation_check_rate=0.0,
        ),
        comparability_key="suite-test:1.0.0",
        total_rollouts=0,
        total_duration_ms=0,
    )

    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    export_json(baseline, str(baseline_path))
    export_json(current, str(current_path))

    class Args:
        baseline = str(baseline_path)
        current = str(current_path)
        threshold = 5.0
        config = None
        output = None
        format = "text"

    exit_code = cmd_compare(Args())
    assert exit_code == 1


def test_cli_export(tmp_path):
    result = SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=70.0,
        grade="B",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=70.0,
                trust_elasticity=70.0,
                grade="B",
                passed=True,
                halted=False,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=False,
            halted_count=0,
            halted_behaviors=[],
            foundation_check_rate=0.0,
        ),
        comparability_key="suite-test:1.0.0",
        total_rollouts=0,
        total_duration_ms=0,
    )

    json_path = tmp_path / "result.json"
    export_json(result, str(json_path))

    class Args:
        input = str(json_path)
        format = "html"
        output = str(tmp_path / "result.html")

    exit_code = cmd_export(Args())
    assert exit_code == 0
    assert (tmp_path / "result.html").exists()
