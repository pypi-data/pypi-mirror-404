"""Tests for artifact capture."""
from harness.artifacts import ArtifactCollector


def test_no_partial_bundle():
    """Transcript exists but tool_traces missing = FAIL."""
    collector = ArtifactCollector()
    collector.record_message("user", "test")
    bundle = collector.finalize("success")

    assert "transcript" in bundle
    assert "tool_traces" in bundle
    assert "repo_diff" in bundle
    assert "test_results" in bundle
    assert "timings" in bundle


def test_tool_trace_complete():
    """Every tool invocation appears in traces."""
    collector = ArtifactCollector()

    for i in range(5):
        collector.record_tool_call(f"tool_{i}", {"arg": i}, f"result_{i}", 100)

    bundle = collector.finalize("success")
    assert len(bundle["tool_traces"]) == 5, "Tool invocation not in traces"
