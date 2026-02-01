"""Tests for E8-S2 bundle capture infrastructure.

These tests verify that score_outcome correctly captures
RunArtifactBundle data from the workspace.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scaffold.scorer import (
    score_outcome,
    OutcomeScore,
    _build_bundle_from_workspace,
    _capture_committed_diff,
)
from harness.types import RunArtifactBundle, GitDiff, TestReport


# --- Fixtures ---


@pytest.fixture
def mock_git_diff() -> GitDiff:
    """Create a mock git diff."""
    return {
        "files_changed": ["src/main.py", "src/utils.py"],
        "insertions": 50,
        "deletions": 10,
        "patch": "diff --git a/src/main.py\n+ added code",
    }


@pytest.fixture
def mock_test_results() -> TestReport:
    """Create mock test results."""
    return {
        "framework": "pytest",
        "passed": 5,
        "failed": 0,
        "skipped": 0,
        "output": "5 passed in 0.5s",
    }


# --- _build_bundle_from_workspace Tests ---


class TestBuildBundleFromWorkspace:
    """Tests for the bundle builder function."""

    def test_builds_complete_bundle(self, mock_git_diff, mock_test_results, tmp_path):
        """Bundle has all required fields."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # All required fields present
        assert "transcript" in bundle
        assert "tool_traces" in bundle
        assert "repo_diff" in bundle
        assert "test_results" in bundle
        assert "timings" in bundle
        assert "exit_code" in bundle

    def test_transcript_has_messages(self, mock_git_diff, mock_test_results, tmp_path):
        """Transcript contains at least user and assistant messages."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        assert len(bundle["transcript"]) >= 2
        roles = {msg["role"] for msg in bundle["transcript"]}
        assert "user" in roles
        assert "assistant" in roles

    def test_tool_traces_from_files_changed(self, mock_git_diff, mock_test_results, tmp_path):
        """Tool traces generated from files changed."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # Should have trace for each file changed
        assert len(bundle["tool_traces"]) == len(mock_git_diff["files_changed"])

        # Each trace should reference a file
        traced_files = {t["arguments"]["path"] for t in bundle["tool_traces"]}
        assert traced_files == set(mock_git_diff["files_changed"])

    def test_repo_diff_preserved(self, mock_git_diff, mock_test_results, tmp_path):
        """Git diff is passed through correctly."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        assert bundle["repo_diff"] == mock_git_diff

    def test_test_results_preserved(self, mock_git_diff, mock_test_results, tmp_path):
        """Test results are passed through correctly."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        assert bundle["test_results"] == mock_test_results

    def test_exit_code_success(self, mock_git_diff, mock_test_results, tmp_path):
        """Exit code 'success' is preserved."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        assert bundle["exit_code"] == "success"

    def test_exit_code_halt(self, mock_git_diff, mock_test_results, tmp_path):
        """Exit code 'halt' is preserved."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="halt",
        )

        assert bundle["exit_code"] == "halt"

    def test_invalid_exit_code_becomes_halt(self, mock_git_diff, mock_test_results, tmp_path):
        """Invalid exit codes default to 'halt'."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="invalid",
        )

        assert bundle["exit_code"] == "halt"

    def test_timings_are_positive(self, mock_git_diff, mock_test_results, tmp_path):
        """Timing values are all positive."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        assert bundle["timings"]["total_ms"] > 0
        assert bundle["timings"]["tool_time_ms"] >= 0
        assert bundle["timings"]["model_time_ms"] >= 0


# --- OutcomeScore with Bundle Tests ---


class TestOutcomeScoreBundle:
    """Tests for bundle field in OutcomeScore."""

    def test_outcome_score_has_bundle_field(self):
        """OutcomeScore dataclass has bundle field."""
        score = OutcomeScore(
            behavior_id="test",
            raw_score=7.0,
            normalized_score=0.7,
            passed_threshold=True,
            git_diff={"files_changed": [], "insertions": 0, "deletions": 0, "patch": ""},
            test_results={"framework": "pytest", "passed": 1, "failed": 0, "skipped": 0, "output": ""},
            scoring_notes=[],
            bundle=None,
        )

        assert hasattr(score, "bundle")
        assert score.bundle is None

    def test_outcome_score_with_bundle(self, mock_git_diff, mock_test_results):
        """OutcomeScore can store a bundle."""
        bundle: RunArtifactBundle = {
            "transcript": [{"role": "user", "content": "test", "timestamp": "2026-01-18T00:00:00Z"}],
            "tool_traces": [],
            "repo_diff": mock_git_diff,
            "test_results": mock_test_results,
            "timings": {"total_ms": 1000, "tool_time_ms": 100, "model_time_ms": 900},
            "exit_code": "success",
        }

        score = OutcomeScore(
            behavior_id="test",
            raw_score=8.0,
            normalized_score=0.8,
            passed_threshold=True,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            scoring_notes=["Good"],
            bundle=bundle,
        )

        assert score.bundle is not None
        assert score.bundle["exit_code"] == "success"


# --- Bundle JSON Serialization Tests ---


class TestBundleSerialization:
    """Tests for bundle JSON serialization."""

    def test_bundle_is_json_serializable(self, mock_git_diff, mock_test_results, tmp_path):
        """Bundle can be serialized to JSON."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # Should not raise
        json_str = json.dumps(bundle)
        assert json_str is not None

    def test_bundle_roundtrip(self, mock_git_diff, mock_test_results, tmp_path):
        """Bundle survives JSON roundtrip."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # Roundtrip through JSON
        json_str = json.dumps(bundle)
        loaded = json.loads(json_str)

        # Key fields preserved
        assert loaded["exit_code"] == bundle["exit_code"]
        assert loaded["repo_diff"]["files_changed"] == bundle["repo_diff"]["files_changed"]
        assert loaded["test_results"]["passed"] == bundle["test_results"]["passed"]


# --- Integration with judge.py ---


class TestBundleJudgeIntegration:
    """Tests for bundle integration with judge scoring."""

    def test_captured_bundle_compatible_with_judge(self, mock_git_diff, mock_test_results, tmp_path):
        """Captured bundle is compatible with gauge.judge functions."""
        from gauge.judge import create_mock_bundle

        # Create bundle from workspace
        captured = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # Create mock bundle
        mock = create_mock_bundle("+ code", "5 passed", "success")

        # Both should have same structure
        assert set(captured.keys()) == set(mock.keys())

    def test_captured_bundle_has_patch(self, mock_git_diff, mock_test_results, tmp_path):
        """Captured bundle includes git patch for GEval evaluation."""
        bundle = _build_bundle_from_workspace(
            workspace_dir=tmp_path,
            git_diff=mock_git_diff,
            test_results=mock_test_results,
            exit_code="success",
        )

        # GEval needs the patch for code quality evaluation
        assert "patch" in bundle["repo_diff"]
        assert bundle["repo_diff"]["patch"] == mock_git_diff["patch"]
