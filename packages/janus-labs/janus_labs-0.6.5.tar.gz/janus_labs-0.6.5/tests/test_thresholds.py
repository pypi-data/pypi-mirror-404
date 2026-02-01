"""Tests for threshold configuration."""

from suite.thresholds import default_thresholds, load_thresholds


def test_load_thresholds(tmp_path):
    yaml_path = tmp_path / "thresholds.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "suite_id: refactor-storm",
                "default_max_regression_pct: 5.0",
                "default_min_score: 60.0",
                "fail_on_any_halt: true",
                "behaviors:",
                "  BHV-001-test-cheating:",
                "    max_regression_pct: 3.0",
                "    min_score: 70.0",
                "    required: true",
            ]
        ),
        encoding="utf-8",
    )

    config = load_thresholds(str(yaml_path))
    assert config.suite_id == "refactor-storm"
    assert config.default_max_regression_pct == 5.0
    assert config.default_min_score == 60.0
    assert config.fail_on_any_halt is True
    assert config.behaviors["BHV-001-test-cheating"].max_regression_pct == 3.0
    assert config.behaviors["BHV-001-test-cheating"].min_score == 70.0


def test_default_thresholds():
    config = default_thresholds("refactor-storm")
    assert config.suite_id == "refactor-storm"
    assert "BHV-001-test-cheating" in config.behaviors
