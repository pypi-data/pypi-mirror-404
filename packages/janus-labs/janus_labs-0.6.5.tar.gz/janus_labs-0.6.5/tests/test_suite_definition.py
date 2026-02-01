"""Tests for BenchmarkSuite definition."""

from forge.behavior import BehaviorSpec
from suite.definition import BenchmarkSuite


def test_suite_creation_and_key():
    behavior = BehaviorSpec(
        behavior_id="BHV-TEST",
        name="Test Behavior",
        description="Test",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    suite = BenchmarkSuite(
        suite_id="refactor-storm",
        version="1.0.0",
        display_name="Refactor Storm",
        description="Suite test",
        behaviors=[behavior],
    )

    assert suite.comparability_key == "refactor-storm:1.0.0"


def test_suite_validation():
    behavior = BehaviorSpec(
        behavior_id="BHV-TEST",
        name="Test Behavior",
        description="Test",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    suite = BenchmarkSuite(
        suite_id="refactor-storm",
        version="1.0",
        display_name="Refactor Storm",
        description="Suite test",
        behaviors=[],
    )

    errors = suite.validate()
    assert "behaviors must be non-empty" in errors
    assert any("version must be valid semver" in err for err in errors)

    suite.behaviors = [behavior]
    suite.version = "1.0.0"
    suite.ensure_valid()
