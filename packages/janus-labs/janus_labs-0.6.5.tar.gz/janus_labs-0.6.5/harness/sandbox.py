"""Filesystem sandbox enforcement for agent writes."""
from pathlib import Path
from typing import Set


class Sandbox:
    """
    Filesystem sandbox that tracks and validates all write operations.
    """

    def __init__(self, allowed_paths: list[str]):
        """
        Args:
            allowed_paths: List of absolute paths agent can write to
        """
        self.allowed_paths: Set[Path] = {Path(p).resolve() for p in allowed_paths}
        self.write_log: list[Path] = []

    def validate_write(self, path: str) -> bool:
        """
        Check if path is within allowed sandbox.

        Returns:
            bool: True if write is allowed
        """
        candidate = Path(path).resolve()
        for allowed in self.allowed_paths:
            if candidate == allowed or allowed in candidate.parents:
                return True

        self.write_log.append(candidate)
        return False

    def get_violations(self) -> list[Path]:
        """Return list of paths written outside sandbox."""
        return list(self.write_log)

    def is_clean(self) -> bool:
        """Return True if no violations occurred."""
        return len(self.write_log) == 0
