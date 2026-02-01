"""Artifact collection for Janus Labs harness."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Callable

from .types import RunArtifactBundle, Message, ToolInvocation, GitDiff, TestReport, Timings


def _run_git(args: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout


class ArtifactCollector:
    """
    Collects all components of a RunArtifactBundle during agent execution.
    """

    def __init__(self):
        self.messages: list[Message] = []
        self.tool_traces: list[ToolInvocation] = []
        self.start_time: float = time.perf_counter()
        self.tool_time_ms: int = 0
        self.repo_diff: GitDiff | None = None
        self.test_results: TestReport | None = None

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_message(self, role: str, content: str) -> None:
        """Record a conversation message."""
        message: Message = {
            "role": role,
            "content": content,
            "timestamp": self._timestamp(),
        }
        self.messages.append(message)

    def record_tool_call(self, tool_name: str, args: dict, result: Any, duration_ms: int) -> None:
        """Record a tool invocation with timing."""
        if not isinstance(result, (str, dict)):
            result = str(result)
        trace: ToolInvocation = {
            "tool_name": tool_name,
            "arguments": args,
            "result": result,
            "duration_ms": max(int(duration_ms), 0),
            "timestamp": self._timestamp(),
        }
        self.tool_traces.append(trace)
        self.tool_time_ms += trace["duration_ms"]

    def capture_git_diff(self, repo_path: str) -> GitDiff:
        """Capture git diff from repo."""
        repo = Path(repo_path).resolve()
        files_changed: list[str] = []
        insertions = 0
        deletions = 0
        patch = ""

        try:
            numstat = _run_git(["diff", "--numstat"], repo)
            if numstat:
                for line in numstat.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        ins, dels, file_path = parts[0], parts[1], parts[2]
                        if ins.isdigit():
                            insertions += int(ins)
                        if dels.isdigit():
                            deletions += int(dels)
                        files_changed.append(file_path)

            name_only = _run_git(["diff", "--name-only"], repo)
            if name_only is not None:
                files_changed = [line for line in name_only.splitlines() if line.strip()]

            patch = _run_git(["diff"], repo) or ""
        except Exception:
            files_changed = []
            insertions = 0
            deletions = 0
            patch = ""

        diff: GitDiff = {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "patch": patch,
        }
        self.repo_diff = diff
        return diff

    def capture_test_results(self, test_output: str, framework: str = "pytest") -> TestReport:
        """Parse test output into TestReport."""
        passed = 0
        failed = 0
        skipped = 0

        if framework == "pytest":
            # Search the full output for the summary line
            # The summary is at the end: "7 passed in 0.02s" or "3 passed, 1 failed"
            passed_match = re.search(r"(\d+)\s+passed", test_output)
            failed_match = re.search(r"(\d+)\s+failed", test_output)
            skipped_match = re.search(r"(\d+)\s+skipped", test_output)
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            if skipped_match:
                skipped = int(skipped_match.group(1))

        report: TestReport = {
            "framework": framework if framework in {"pytest", "jest", "other"} else "other",
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "output": test_output,
        }
        self.test_results = report
        return report

    def create_tool_wrapper(self, original_tool: Callable) -> Callable:
        """
        Wrap a tool function to automatically record invocations.
        """
        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            result = original_tool(*args, **kwargs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            call_args = {"args": list(args), "kwargs": kwargs}
            self.record_tool_call(original_tool.__name__, call_args, result, duration_ms)
            return result

        return wrapped

    def finalize(self, exit_code: str) -> RunArtifactBundle:
        """
        Finalize and return complete bundle.

        Guarantees:
        - All 5 components present
        - No None values in required fields
        """
        tool_time_ms = max(int(self.tool_time_ms), 1)
        elapsed_ms = int((time.perf_counter() - self.start_time) * 1000)
        total_ms = max(elapsed_ms, tool_time_ms, 1)
        model_time_ms = max(total_ms - tool_time_ms, 1)

        timings: Timings = {
            "total_ms": total_ms,
            "tool_time_ms": tool_time_ms,
            "model_time_ms": model_time_ms,
        }

        repo_diff = self.repo_diff or {
            "files_changed": [],
            "insertions": 0,
            "deletions": 0,
            "patch": "",
        }
        test_results = self.test_results or {
            "framework": "pytest",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "output": "",
        }

        if exit_code not in {"success", "timeout", "crash", "halt"}:
            exit_code = "crash"

        bundle: RunArtifactBundle = {
            "transcript": list(self.messages),
            "tool_traces": list(self.tool_traces),
            "repo_diff": repo_diff,
            "test_results": test_results,
            "timings": timings,
            "exit_code": exit_code,
        }
        return bundle
