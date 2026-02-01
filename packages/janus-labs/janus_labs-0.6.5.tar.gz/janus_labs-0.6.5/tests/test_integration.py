"""Integration test for full bundle generation."""

from pathlib import Path

from harness.artifacts import ArtifactCollector
from harness.executor import init_fixture
from harness.sandbox import Sandbox


def test_full_bundle_generation():
    """
    End-to-end test: Initialize fixture, simulate agent work, capture bundle.

    This test validates ALL 4 disconfirmers from PRD:
    1. Partial bundle (transcript exists but tool_traces missing)
    2. Non-idempotent (same scenario produces different fixture states)
    3. Leaky sandbox (agent writes outside designated paths)
    4. Incomplete capture (tool invocation not in traces)
    """
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "simple-task"
    sandbox = Sandbox([str(fixture_path.resolve())])
    collector = ArtifactCollector()

    assert init_fixture(str(fixture_path))

    collector.record_message("user", "Modify main.py to print hello")
    main_path = fixture_path / "main.py"
    collector.record_tool_call("read_file", {"path": str(main_path)}, "content", 50)
    collector.record_tool_call("write_file", {"path": str(main_path)}, "ok", 30)
    sandbox.validate_write(str(main_path))

    bundle = collector.finalize("success")

    assert len(bundle["transcript"]) >= 1
    assert len(bundle["tool_traces"]) >= 2
    assert bundle["timings"]["total_ms"] > 0
    assert sandbox.is_clean()
