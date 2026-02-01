"""Tests for baseline CLI command."""

from cli.main import cmd_baseline
from suite.export.json_export import export_json
from suite.result import GovernanceFlags, SuiteResult


def _suite_result() -> SuiteResult:
    return SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=90.0,
        grade="S",
        behavior_scores=[],
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


def test_cli_baseline_update_and_show(tmp_path, capsys):
    result = _suite_result()
    result_path = tmp_path / "result.json"
    export_json(result, str(result_path))

    class UpdateArgs:
        baseline_command = "update"
        result = str(result_path)
        output = str(tmp_path / "baseline.json")
        force = False

    exit_code = cmd_baseline(UpdateArgs())
    assert exit_code == 0
    assert (tmp_path / "baseline.json").exists()

    class ShowArgs:
        baseline_command = "show"
        baseline = str(tmp_path / "baseline.json")

    exit_code = cmd_baseline(ShowArgs())
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "suite-test" in captured.out.lower()
