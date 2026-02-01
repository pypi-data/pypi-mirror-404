"""BenchmarkSuite schema for Janus Labs."""

from dataclasses import dataclass
import re
from typing import List

from forge.behavior import BehaviorSpec


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class BenchmarkSuite:
    """A collection of behaviors to benchmark together."""
    suite_id: str
    version: str
    display_name: str
    description: str
    behaviors: List[BehaviorSpec]
    rollouts_per_behavior: int = 10
    judge_model: str = "claude-opus-4-5-20251101"
    timeout_per_behavior_ms: int = 60000

    @property
    def comparability_key(self) -> str:
        """Key for comparing results across runs."""
        return f"{self.suite_id}:{self.version}"

    def validate(self) -> list[str]:
        """Return validation errors for this suite."""
        errors: list[str] = []
        if not self.suite_id:
            errors.append("suite_id is required")
        if not self.display_name:
            errors.append("display_name is required")
        if not self.description:
            errors.append("description is required")
        if not self.behaviors:
            errors.append("behaviors must be non-empty")
        if not SEMVER_RE.match(self.version or ""):
            errors.append("version must be valid semver (X.Y.Z)")
        if self.rollouts_per_behavior <= 0:
            errors.append("rollouts_per_behavior must be > 0")
        return errors

    def ensure_valid(self) -> None:
        """Raise ValueError if suite is invalid."""
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
