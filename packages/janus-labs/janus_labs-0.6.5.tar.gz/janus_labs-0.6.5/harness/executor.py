"""Execution helpers for Janus Labs harness."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Sequence


def _run_git(args: Sequence[str], cwd: Path) -> bool:
    try:
        subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def init_fixture(fixture_path: str) -> bool:
    """
    Initialize fixture repo to clean state.

    Guarantees:
    - git reset --hard HEAD
    - git clean -fd (remove untracked files)
    - Returns True if successful

    Args:
        fixture_path: Absolute path to fixture repo

    Returns:
        bool: True if initialization succeeded
    """
    repo_path = Path(fixture_path).resolve()
    if not repo_path.exists():
        return False

    if not (repo_path / ".git").exists():
        return False

    if not _run_git(["reset", "--hard", "HEAD"], repo_path):
        return False

    if not _run_git(["clean", "-fd"], repo_path):
        return False

    return True
