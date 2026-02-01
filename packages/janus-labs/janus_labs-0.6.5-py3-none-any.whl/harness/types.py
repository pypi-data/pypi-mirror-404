"""Typed structures for RunArtifactBundle capture."""
from typing import TypedDict, Literal


class Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str  # ISO8601


class ToolInvocation(TypedDict):
    tool_name: str
    arguments: dict
    result: str | dict
    duration_ms: int
    timestamp: str  # ISO8601


class GitDiff(TypedDict):
    files_changed: list[str]
    insertions: int
    deletions: int
    patch: str  # Full diff output


class TestReport(TypedDict):
    framework: Literal["pytest", "jest", "other"]
    passed: int
    failed: int
    skipped: int
    output: str  # Full test output


class Timings(TypedDict):
    total_ms: int
    tool_time_ms: int
    model_time_ms: int


class RunArtifactBundle(TypedDict):
    transcript: list[Message]
    tool_traces: list[ToolInvocation]
    repo_diff: GitDiff
    test_results: TestReport
    timings: Timings
    exit_code: Literal["success", "timeout", "crash", "halt"]
