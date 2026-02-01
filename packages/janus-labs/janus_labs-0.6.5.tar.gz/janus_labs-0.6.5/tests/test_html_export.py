"""Tests for HTML export."""

from suite.export.html import export_html
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult


def test_html_export(tmp_path):
    result = SuiteResult(
        suite_id="suite-test",
        suite_version="1.0.0",
        config_fingerprint="abc123",
        timestamp="2025-12-25T00:00:00Z",
        headline_score=82.5,
        grade="A",
        behavior_scores=[
            BehaviorScore(
                behavior_id="BHV-1",
                name="Behavior One",
                score=82.5,
                trust_elasticity=82.5,
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
        comparability_key="suite-test:1.0.0",
        total_rollouts=10,
        total_duration_ms=1000,
    )

    output_path = tmp_path / "report.html"
    export_html(result, str(output_path))

    html = output_path.read_text(encoding="utf-8")
    assert "<html" in html.lower()
    assert "82.5" in html
    assert "Behavior One" in html
    assert "http://" not in html
    assert "https://" not in html
