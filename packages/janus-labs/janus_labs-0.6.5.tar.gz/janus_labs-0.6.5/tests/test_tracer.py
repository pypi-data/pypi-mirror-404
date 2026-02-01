"""Tests for Phoenix tracer."""

from probe.tracer import PhoenixTracer


def test_phoenix_tracer_basic():
    """PhoenixTracer creates and exports traces."""
    tracer = PhoenixTracer()

    tracer.start_trace("Fix the bug", mutation="task_variation")
    tracer.record_tool_call("read_file", {"path": "test.py"}, "content", 50)
    tracer.record_message("user", "Fix it")
    tracer.end_trace("success")

    traces = tracer.export_traces()
    assert len(traces) == 1
    assert traces[0]["task"] == "Fix the bug"
    assert traces[0]["mutation"] == "task_variation"
    assert len(traces[0]["spans"]) == 2
