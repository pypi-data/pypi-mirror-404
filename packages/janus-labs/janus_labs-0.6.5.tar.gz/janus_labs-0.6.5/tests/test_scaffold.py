"""Tests for task scaffold system."""

import json
import pytest
from pathlib import Path
import tempfile

from scaffold.workspace import init_workspace, load_task_metadata, TaskMetadata
from forge.behavior import BehaviorSpec
from suite.definition import BenchmarkSuite


@pytest.fixture
def sample_suite() -> BenchmarkSuite:
    return BenchmarkSuite(
        suite_id="test-suite",
        version="1.0.0",
        display_name="Test Suite",
        description="For testing",
        behaviors=[
            BehaviorSpec(
                behavior_id="BHV-TEST-001",
                name="Test Behavior",
                description="Test description",
                rubric={1: "Bad", 5: "OK", 10: "Great"},
                threshold=5.0,
                disconfirmers=["fail"],
                taxonomy_code="T-1.00",
            )
        ],
        rollouts_per_behavior=1,
    )


class TestWorkspaceInit:
    def test_creates_metadata_file(self, sample_suite: BenchmarkSuite):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "workspace"
            behavior = sample_suite.behaviors[0]

            metadata = init_workspace(target, sample_suite, behavior)

            assert (target / ".janus-task.json").exists()
            assert metadata.suite_id == "test-suite"
            assert metadata.behavior_id == "BHV-TEST-001"

    def test_creates_directories(self, sample_suite: BenchmarkSuite):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "workspace"
            behavior = sample_suite.behaviors[0]

            init_workspace(target, sample_suite, behavior)

            assert (target / "src").is_dir()
            assert (target / "tests").is_dir()

    def test_creates_readme(self, sample_suite: BenchmarkSuite):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "workspace"
            behavior = sample_suite.behaviors[0]

            init_workspace(target, sample_suite, behavior)

            readme = target / "README.md"
            assert readme.exists()
            content = readme.read_text()
            assert "BHV-TEST-001" in content
            assert "Test Behavior" in content


class TestTaskMetadata:
    def test_to_dict_roundtrip(self):
        metadata = TaskMetadata(
            suite_id="suite",
            behavior_id="behavior",
            behavior_name="name",
            behavior_description="desc",
            threshold=7.0,
            rubric={1: "bad", 10: "good"},
            workspace_path="/tmp/test",
            initialized_at="2026-01-11T00:00:00Z",
        )

        data = metadata.to_dict()
        restored = TaskMetadata.from_dict(data)

        assert restored.suite_id == metadata.suite_id
        assert restored.threshold == metadata.threshold

    def test_load_from_workspace(self, sample_suite: BenchmarkSuite):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "workspace"
            behavior = sample_suite.behaviors[0]

            init_workspace(target, sample_suite, behavior)

            loaded = load_task_metadata(target)
            assert loaded is not None
            assert loaded.behavior_id == "BHV-TEST-001"

    def test_load_nonexistent_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = load_task_metadata(Path(tmpdir))
            assert loaded is None
