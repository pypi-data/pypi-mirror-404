"""Tests for janus-labs init command."""
import pytest
import tempfile
from pathlib import Path
from cli.main import cmd_init
import argparse


class TestCmdInit:
    """Tests for the init command (JL-104: all behaviors by default)."""

    def test_init_creates_all_behavior_workspaces(self):
        """Test successful initialization of all behaviors in suite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 0
            assert output.exists()

            # Should have 5 behavior subdirectories
            behavior_dirs = [d for d in output.iterdir() if d.is_dir()]
            assert len(behavior_dirs) == 5

            # Each should have .janus-task.json
            for behavior_dir in behavior_dirs:
                assert (behavior_dir / ".janus-task.json").exists()
                assert (behavior_dir / "README.md").exists()

    def test_init_creates_expected_behaviors(self):
        """Test that all expected behaviors are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 0

            expected_behaviors = [
                "BHV-001-test-cheating",
                "BHV-002-refactor-complexity",
                "BHV-003-error-handling",
                "O-2.01-instruction-adherence",
                "O-3.01-code-quality",
            ]
            for behavior_id in expected_behaviors:
                assert (output / behavior_id).exists(), f"Missing {behavior_id}"

    def test_init_unknown_suite(self, capsys):
        """Test error on unknown suite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                suite="nonexistent-suite",
                output=str(Path(tmpdir) / "janus-task")
            )
            result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "Unknown suite" in captured.err
            assert "Try:" in captured.err

    def test_init_directory_not_empty(self, capsys):
        """Test error when directory is not empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            output.mkdir()
            (output / "existing-file.txt").write_text("content")

            args = argparse.Namespace(
                suite="refactor-storm",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "not empty" in captured.err
            assert "Try:" in captured.err

    def test_init_gitignore_created(self):
        """Test that .gitignore is created in each behavior workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 0

            # Check first behavior dir has gitignore with expected entries
            first_behavior = output / "BHV-001-test-cheating"
            gitignore = first_behavior / ".gitignore"
            assert gitignore.exists()
            content = gitignore.read_text()
            assert "result.json" in content
            assert "*.bundle.json" in content
