"""
Stub types for standalone Janus Labs operation.

When running within the AoP monorepo, the full Janus Protocol is available.
For standalone use, these stubs provide minimal functionality.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TrustScore:
    """Trust score for an agent session."""

    value: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0

    @classmethod
    def default(cls) -> "TrustScore":
        """Return default trust score."""
        return cls(value=0.7, confidence=0.5)


@dataclass
class GovernanceState:
    """Minimal governance state for standalone operation."""

    iteration_count: int = 1
    halted: bool = False
    trust_score: Optional[TrustScore] = None


def foundation_check(
    iteration_count: int,
    same_pattern: bool = False,
    merge_ready: bool = False,
    current_approach: Optional[str] = None,
    approach_history: Optional[List[str]] = None,
    confidence: Optional[float] = None,
    confidence_history: Optional[List[float]] = None,
) -> dict:
    """
    Stub foundation check for standalone operation.

    Returns PASS for iterations 1-2, WARN for iteration 3+.
    Full implementation available in mcp-janus.

    Args:
        iteration_count: Current iteration number
        same_pattern: Whether the same approach is being repeated
        merge_ready: Whether work is ready for merge
        current_approach: Description of current approach
        approach_history: List of previous approaches
        confidence: Current confidence level
        confidence_history: History of confidence levels

    Returns:
        dict with result, trigger, signals, and recommendation
    """
    _ = merge_ready, current_approach, approach_history, confidence, confidence_history

    if iteration_count >= 3:
        return {
            "result": "HALT" if same_pattern else "WARN",
            "trigger": "iteration",
            "signals": {"iteration": iteration_count},
            "recommendation": "Consider decomposing the task",
        }
    return {
        "result": "PASS",
        "trigger": "none",
        "signals": {"iteration": iteration_count},
        "recommendation": "Proceed",
    }


def handle_escalation(result: dict, context: dict) -> dict:
    """
    Stub escalation handler - logs but takes no action.

    Args:
        result: The governance check result
        context: Additional context for escalation

    Returns:
        dict with escalation_id and action taken
    """
    _ = result, context
    return {"escalation_id": None, "action": "logged"}


def infer_confidence(text: str) -> Tuple[float, str]:
    """
    Stub confidence inference - returns moderate confidence.

    Args:
        text: Text to analyze for confidence signals

    Returns:
        Tuple of (confidence_value, confidence_label)
    """
    _ = text
    return (0.7, "moderate")


# In-memory storage for standalone operation
_memory_store: dict = {}


def read_tier(tier: str, target_dir: str = ".") -> dict:
    """
    Stub memory tier reader - uses in-memory storage.

    Args:
        tier: Memory tier name (e.g., "governance")
        target_dir: Target directory (ignored in stub)

    Returns:
        Stored data for the tier, or empty dict
    """
    _ = target_dir
    return _memory_store.get(tier, {})


def write_tier(tier: str, data: dict, target_dir: str = ".") -> Tuple[bool, List[str]]:
    """
    Stub memory tier writer - uses in-memory storage.

    Args:
        tier: Memory tier name (e.g., "governance")
        data: Data to store
        target_dir: Target directory (ignored in stub)

    Returns:
        Tuple of (success, error_list)
    """
    _ = target_dir
    _memory_store[tier] = data
    return (True, [])
