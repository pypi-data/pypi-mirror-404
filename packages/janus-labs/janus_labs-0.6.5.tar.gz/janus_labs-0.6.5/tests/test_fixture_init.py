"""Tests for fixture initialization."""
from pathlib import Path
import subprocess

from harness.executor import init_fixture


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "simple-task"


def _git_output(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_repo_state(path: Path) -> tuple[str, tuple[str, ...]]:
    sha = _git_output(["rev-parse", "HEAD"], path)
    files = tuple(
        line for line in _git_output(["ls-files"], path).splitlines() if line.strip()
    )
    return sha, files


def test_fixture_idempotent():
    """Same scenario produces identical fixture states."""
    states = []
    for _ in range(10):
        assert init_fixture(str(FIXTURE_PATH.resolve()))
        states.append(get_repo_state(FIXTURE_PATH))
    assert len(set(states)) == 1, "Fixture init not idempotent"


def test_fixture_clean_state():
    """No uncommitted or untracked files remain after init."""
    assert init_fixture(str(FIXTURE_PATH.resolve()))
    status = _git_output(["status", "--porcelain"], FIXTURE_PATH)
    assert status == "", "Fixture repo not clean after init"
