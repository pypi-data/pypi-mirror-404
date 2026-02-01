"""Tests for LLM-as-judge scoring (E8-S3).

These tests verify the judge.py module without requiring
actual API calls (uses mocking for GEval).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from forge.behavior import BehaviorSpec
from gauge.judge import (
    JudgeResult,
    score_with_judge,
    create_mock_bundle,
    load_bundle_from_file,
)


# --- Fixtures ---


@pytest.fixture
def sample_behavior():
    """Create a sample BehaviorSpec for testing."""
    return BehaviorSpec(
        behavior_id="test-behavior",
        name="Test Behavior",
        description="A test behavior for unit testing",
        rubric={
            1: "Completely wrong",
            5: "Partially correct",
            10: "Perfect solution",
        },
        threshold=7.0,
        disconfirmers=["Fails to compile", "No tests"],
        taxonomy_code="TEST.001",
    )


@pytest.fixture
def sample_bundle():
    """Create a sample RunArtifactBundle for testing."""
    return create_mock_bundle(
        code_diff="+ def hello(): return 'world'",
        test_output="All tests passed",
        exit_code="success",
    )


# --- JudgeResult Tests ---


class TestJudgeResult:
    """Tests for the JudgeResult dataclass."""

    def test_judge_result_fields(self):
        """JudgeResult has all required fields."""
        result = JudgeResult(
            geval_score=0.85,
            geval_score_10=8.5,
            reason="Good solution",
            outcome_score=0.9,
            combined_score=0.87,
            combined_score_10=8.7,
            model="gpt-4o",
        )

        assert result.geval_score == 0.85
        assert result.geval_score_10 == 8.5
        assert result.reason == "Good solution"
        assert result.outcome_score == 0.9
        assert result.combined_score == 0.87
        assert result.combined_score_10 == 8.7
        assert result.model == "gpt-4o"

    def test_score_ranges(self):
        """Scores are within expected ranges."""
        result = JudgeResult(
            geval_score=0.5,
            geval_score_10=5.0,
            reason="Average",
            outcome_score=0.6,
            combined_score=0.56,
            combined_score_10=5.6,
            model="gpt-4o",
        )

        assert 0.0 <= result.geval_score <= 1.0
        assert 0.0 <= result.geval_score_10 <= 10.0
        assert 0.0 <= result.outcome_score <= 1.0
        assert 0.0 <= result.combined_score <= 1.0
        assert 0.0 <= result.combined_score_10 <= 10.0


# --- create_mock_bundle Tests ---


class TestCreateMockBundle:
    """Tests for the create_mock_bundle helper."""

    def test_mock_bundle_structure(self):
        """Mock bundle has required structure."""
        bundle = create_mock_bundle("+ code", "tests passed", "success")

        assert "transcript" in bundle
        assert "tool_traces" in bundle
        assert "repo_diff" in bundle
        assert "test_results" in bundle
        assert "timings" in bundle
        assert "exit_code" in bundle

    def test_mock_bundle_transcript(self):
        """Transcript has user and assistant messages."""
        bundle = create_mock_bundle("+ code", "tests passed", "success")

        assert len(bundle["transcript"]) >= 2
        roles = [msg["role"] for msg in bundle["transcript"]]
        assert "user" in roles
        assert "assistant" in roles

    def test_mock_bundle_repo_diff(self):
        """Repo diff contains the provided code diff."""
        code_diff = "+ def foo(): pass"
        bundle = create_mock_bundle(code_diff, "ok", "success")

        assert bundle["repo_diff"]["patch"] == code_diff
        assert bundle["repo_diff"]["insertions"] == 1  # One line

    def test_mock_bundle_test_results(self):
        """Test results contain expected fields."""
        bundle = create_mock_bundle("code", "12 passed", "success")

        assert bundle["test_results"]["output"] == "12 passed"
        assert bundle["test_results"]["passed"] >= 0
        assert bundle["test_results"]["failed"] >= 0

    def test_mock_bundle_exit_codes(self):
        """Exit code is correctly set."""
        success_bundle = create_mock_bundle("code", "ok", "success")
        error_bundle = create_mock_bundle("code", "fail", "error")
        halt_bundle = create_mock_bundle("code", "halt", "halt")

        assert success_bundle["exit_code"] == "success"
        assert error_bundle["exit_code"] == "error"
        assert halt_bundle["exit_code"] == "halt"


# --- load_bundle_from_file Tests ---


class TestLoadBundleFromFile:
    """Tests for the load_bundle_from_file function."""

    def test_load_valid_bundle(self, tmp_path):
        """Can load a valid bundle from JSON file."""
        bundle_data = {
            "transcript": [{"role": "user", "content": "hi"}],
            "tool_traces": [],
            "repo_diff": {"files_changed": [], "insertions": 0, "deletions": 0, "patch": ""},
            "test_results": {"framework": "pytest", "passed": 1, "failed": 0, "skipped": 0, "output": ""},
            "timings": {"total_ms": 100, "tool_time_ms": 50, "model_time_ms": 50},
            "exit_code": "success",
        }

        bundle_file = tmp_path / "bundle.json"
        bundle_file.write_text(json.dumps(bundle_data))

        loaded = load_bundle_from_file(str(bundle_file))

        assert loaded["exit_code"] == "success"
        assert loaded["test_results"]["passed"] == 1

    def test_load_missing_file(self, tmp_path):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_bundle_from_file(str(tmp_path / "nonexistent.json"))

    def test_load_incomplete_bundle(self, tmp_path):
        """Raises ValueError for bundle missing required fields."""
        incomplete_data = {
            "transcript": [],
            # Missing other required fields
        }

        bundle_file = tmp_path / "incomplete.json"
        bundle_file.write_text(json.dumps(incomplete_data))

        with pytest.raises(ValueError) as exc_info:
            load_bundle_from_file(str(bundle_file))

        assert "missing required fields" in str(exc_info.value).lower()


# --- score_with_judge Tests ---


class TestScoreWithJudge:
    """Tests for the score_with_judge function."""

    def test_requires_openai_api_key_for_gpt(self, sample_behavior, sample_bundle, monkeypatch):
        """Raises ValueError if OPENAI_API_KEY not set for GPT models."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            score_with_judge(sample_behavior, sample_bundle, 0.8, model="gpt-4o")

        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_requires_anthropic_api_key_for_claude(self, sample_behavior, sample_bundle, monkeypatch):
        """Raises ValueError if ANTHROPIC_API_KEY not set for Claude models."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            score_with_judge(sample_behavior, sample_bundle, 0.8, model="claude-3-5-sonnet")

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_combined_score_weighting(
        self, mock_test_case, mock_metric, sample_behavior, sample_bundle, monkeypatch
    ):
        """Combined score uses correct weighting (40% outcome, 60% geval)."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Mock the GEval metric
        mock_geval = MagicMock()
        mock_geval.score = 0.8  # GEval returns 0.8
        mock_geval.reason = "Good implementation"
        mock_metric.return_value = mock_geval

        outcome_score = 0.9  # Outcome score is 0.9
        result = score_with_judge(
            sample_behavior, sample_bundle, outcome_score, model="gpt-4o"
        )

        # Combined should be: 0.4 * 0.9 + 0.6 * 0.8 = 0.36 + 0.48 = 0.84
        expected_combined = 0.4 * outcome_score + 0.6 * mock_geval.score
        assert result.combined_score == pytest.approx(expected_combined, rel=0.01)

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_custom_outcome_weight(
        self, mock_test_case, mock_metric, sample_behavior, sample_bundle, monkeypatch
    ):
        """Custom outcome weight is respected."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_geval = MagicMock()
        mock_geval.score = 0.7
        mock_geval.reason = "OK"
        mock_metric.return_value = mock_geval

        outcome_score = 0.5
        outcome_weight = 0.6  # 60% outcome, 40% geval (custom)

        result = score_with_judge(
            sample_behavior,
            sample_bundle,
            outcome_score,
            model="gpt-4o",
            outcome_weight=outcome_weight,
        )

        # Combined: 0.6 * 0.5 + 0.4 * 0.7 = 0.30 + 0.28 = 0.58
        expected = outcome_weight * outcome_score + (1 - outcome_weight) * mock_geval.score
        assert result.combined_score == pytest.approx(expected, rel=0.01)

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_result_includes_model_name(
        self, mock_test_case, mock_metric, sample_behavior, sample_bundle, monkeypatch
    ):
        """JudgeResult includes the model name used."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_geval = MagicMock()
        mock_geval.score = 0.75
        mock_geval.reason = "Good"
        mock_metric.return_value = mock_geval

        result = score_with_judge(
            sample_behavior, sample_bundle, 0.8, model="gpt-4o-mini"
        )

        assert result.model == "gpt-4o-mini"

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_geval_score_scaled_to_10(
        self, mock_test_case, mock_metric, sample_behavior, sample_bundle, monkeypatch
    ):
        """GEval score is correctly scaled to 0-10 range."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_geval = MagicMock()
        mock_geval.score = 0.75  # 0-1 scale
        mock_geval.reason = "Good"
        mock_metric.return_value = mock_geval

        result = score_with_judge(sample_behavior, sample_bundle, 0.8, model="gpt-4o")

        assert result.geval_score == 0.75
        assert result.geval_score_10 == 7.5  # Scaled to 10

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_reason_fallback(
        self, mock_test_case, mock_metric, sample_behavior, sample_bundle, monkeypatch
    ):
        """Falls back to default reason if GEval provides none."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_geval = MagicMock()
        mock_geval.score = 0.5
        mock_geval.reason = None  # No reason provided
        mock_metric.return_value = mock_geval

        result = score_with_judge(sample_behavior, sample_bundle, 0.8, model="gpt-4o")

        assert result.reason == "No explanation provided"


# --- Integration-like Tests (still mocked) ---


class TestJudgeIntegration:
    """Integration-style tests for the judge scoring flow."""

    @patch("gauge.judge.create_geval_metric")
    @patch("gauge.judge.behavior_to_test_case")
    def test_full_scoring_flow(
        self, mock_test_case, mock_metric, sample_behavior, monkeypatch
    ):
        """Full judge scoring flow works end-to-end."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create bundle
        bundle = create_mock_bundle(
            code_diff="+ def solve(): return 42",
            test_output="5 passed, 0 failed",
            exit_code="success",
        )

        # Mock GEval
        mock_geval = MagicMock()
        mock_geval.score = 0.85
        mock_geval.reason = "Clean implementation with proper structure"
        mock_metric.return_value = mock_geval

        # Score
        result = score_with_judge(
            behavior=sample_behavior,
            bundle=bundle,
            outcome_score=0.9,
            model="gpt-4o",
        )

        # Verify result structure
        assert isinstance(result, JudgeResult)
        assert 0 <= result.geval_score <= 1
        assert 0 <= result.geval_score_10 <= 10
        assert 0 <= result.combined_score <= 1
        assert 0 <= result.combined_score_10 <= 10
        assert len(result.reason) > 0
        assert result.model == "gpt-4o"

        # Verify metric was configured (with model parameter)
        mock_metric.assert_called_once_with(sample_behavior, model="gpt-4o")
        mock_geval.measure.assert_called_once()
