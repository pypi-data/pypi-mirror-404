"""Tests for sandbox isolation."""
from pathlib import Path

from harness.sandbox import Sandbox


def test_sandbox_leak_detection():
    """Agent writes outside designated paths are detected."""
    sandbox = Sandbox(["/tmp/allowed"])
    assert sandbox.validate_write("/tmp/allowed/file.txt") is True
    assert sandbox.validate_write("/etc/passwd") is False
    assert not sandbox.is_clean()
    assert Path("/etc/passwd").resolve() in sandbox.get_violations()
