"""Behavior specification types for Janus Labs."""

from dataclasses import dataclass
from typing import TypedDict


class RubricLevel(TypedDict):
    """Scoring guidance for a rubric level."""
    score: int  # 1-10
    description: str


@dataclass
class BehaviorSpec:
    """
    A falsifiable behavior specification.

    Behaviors are discovered by Probe, formalized in Forge,
    and measured by Gauge.
    """
    behavior_id: str
    name: str
    description: str
    rubric: dict[int, str]
    threshold: float
    disconfirmers: list[str]
    taxonomy_code: str
    version: str = "1.0.0"

    def get_rubric_prompt(self) -> str:
        """Generate rubric prompt for LLM judge."""
        lines = ["Score the following behavior on a 1-10 scale:\n"]
        for score in sorted(self.rubric.keys()):
            lines.append(f"- Score {score}: {self.rubric[score]}")
        return "\n".join(lines)
