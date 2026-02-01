"""Tests for JSON export round-trip."""

from suite.export.json_export import export_json, load_json
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult


def test_json_export_roundtrip(tmp_path):
    result = SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=75.0,
        grade="B",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=75.0,
                trust_elasticity=75.0,
                grade="B",
                passed=True,
                halted=False,
            )
        ],
        governance_flags=GovernanceFlags(
            any_halted=False,
            halted_count=0,
            halted_behaviors=[],
            foundation_check_rate=0.2,
        ),
        comparability_key="suite-test:1.0.0",
        total_rollouts=10,
        total_duration_ms=1000,
    )

    output_path = tmp_path / "result.json"
    export_json(result, str(output_path))

    loaded = load_json(str(output_path))
    assert loaded.suite_id == result.suite_id
    assert loaded.headline_score == result.headline_score
    assert loaded.behavior_scores[0].behavior_id == "BHV-1"
