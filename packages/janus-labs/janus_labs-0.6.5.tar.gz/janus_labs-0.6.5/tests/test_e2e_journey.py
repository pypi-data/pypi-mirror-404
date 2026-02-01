"""End-to-end journey test: init -> score -> submit (JL-104 updated)."""
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path


class TestE2EJourney:
    """Full user journey tests."""

    def test_init_creates_all_behaviors(self):
        """Test that init creates all behavior workspaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            # Use same Python as test runner to ensure deps are available
            result = subprocess.run(
                [sys.executable, "-m", "janus_labs", "init",
                 "--output", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Init failed: {result.stderr}"
            assert workspace.exists()

            # Should have 5 behavior subdirectories
            expected_behaviors = [
                "BHV-001-test-cheating",
                "BHV-002-refactor-complexity",
                "BHV-003-error-handling",
                "O-2.01-instruction-adherence",
                "O-3.01-code-quality",
            ]
            for behavior_id in expected_behaviors:
                behavior_dir = workspace / behavior_id
                assert behavior_dir.exists(), f"Missing {behavior_id}"
                assert (behavior_dir / ".janus-task.json").exists()

    def test_init_score_flow(self):
        """Test the complete init -> modify -> score flow for one behavior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            # Step 1: Init (creates all behaviors)
            result = subprocess.run(
                [sys.executable, "-m", "janus_labs", "init",
                 "--output", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Step 2: Work in one behavior directory
            behavior_dir = workspace / "BHV-002-refactor-complexity"
            assert behavior_dir.exists()

            # Step 3: Make a change and commit
            solution_file = behavior_dir / "solution.py"
            solution_file.write_text("# Refactored solution\ndef calculate():\n    return 42\n")
            subprocess.run(["git", "add", "."], cwd=behavior_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Add solution"], cwd=behavior_dir, capture_output=True)

            # Step 4: Score
            result = subprocess.run(
                [sys.executable, "-m", "janus_labs", "score",
                 "--workspace", str(behavior_dir)],
                capture_output=True, text=True,
                cwd=cwd
            )
            # Score may pass or fail based on solution quality, but should not error
            # The command returns 0 for PASS, 1 for FAIL - both are valid outcomes
            assert result.returncode in [0, 1], f"Score errored: {result.stderr}"
            # Should show the new banner format (JL-102)
            assert "SCORE:" in result.stdout or "Grade:" in result.stdout

    def test_status_command(self):
        """Test status command in behavior workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            # Init first
            subprocess.run(
                [sys.executable, "-m", "janus_labs", "init",
                 "--output", str(workspace)],
                capture_output=True,
                cwd=cwd
            )

            # Then status in a specific behavior dir
            behavior_dir = workspace / "BHV-002-refactor-complexity"
            result = subprocess.run(
                [sys.executable, "-m", "janus_labs", "status",
                 "--workspace", str(behavior_dir)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Status failed: {result.stderr}"
            assert "BHV-002" in result.stdout
            assert "refactor-storm" in result.stdout

    def test_status_not_in_workspace(self):
        """Test status command outside workspace shows helpful error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(__file__).parent.parent

            result = subprocess.run(
                [sys.executable, "-m", "janus_labs", "status",
                 "--workspace", tmpdir],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 1
            assert "Not in a Janus workspace" in result.stderr or "No .janus-task.json" in result.stderr
            assert "Try:" in result.stderr
