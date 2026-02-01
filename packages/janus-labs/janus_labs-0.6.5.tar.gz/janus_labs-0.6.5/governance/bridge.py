"""Bridge between Janus v3.6 governance and Janus Labs Gauge layer."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
from typing import List, Optional

# Try to import from mcp-janus (full installation)
# Fall back to stubs for standalone operation
try:
    MCP_JANUS_PATH = Path(__file__).resolve().parents[2] / "mcp-janus"
    if MCP_JANUS_PATH.exists() and str(MCP_JANUS_PATH) not in sys.path:
        sys.path.insert(0, str(MCP_JANUS_PATH))
    from tools import foundation_check, handle_escalation, infer_confidence  # noqa: E402
except ImportError:
    # Standalone mode - use stubs
    from janus_types import foundation_check, handle_escalation, infer_confidence  # noqa: E402


class GovernanceDecision(Enum):
    """Governance decision outcomes."""
    PASS = "pass"
    WARN = "warn"
    HALT = "halt"


@dataclass
class GovernanceContext:
    """Context for governance evaluation during rollout."""
    rollout_index: int
    behavior_id: str
    current_approach: Optional[str] = None
    approach_history: Optional[List[str]] = None
    reasoning_text: Optional[str] = None
    target_dir: str = "."


@dataclass
class GovernanceResult:
    """Result of governance check."""
    decision: GovernanceDecision
    trigger: Optional[str]
    signals: dict
    recommendation: str
    escalation_id: Optional[str] = None
    should_halt: bool = False


def _to_decision(result_value: str) -> GovernanceDecision:
    normalized = result_value.upper()
    if normalized == "HALT":
        return GovernanceDecision.HALT
    if normalized == "WARN":
        return GovernanceDecision.WARN
    return GovernanceDecision.PASS


def check_governance(context: GovernanceContext) -> GovernanceResult:
    """
    Evaluate governance signals for a rollout iteration.

    Integrates Janus v3.6 foundation_check with rollout-specific context.

    Args:
        context: GovernanceContext with rollout state

    Returns:
        GovernanceResult with decision and metadata
    """
    confidence = None
    if context.reasoning_text:
        confidence, _ = infer_confidence(context.reasoning_text)

    confidence_history = None
    if context.approach_history and len(context.approach_history) > 1:
        count = len(context.approach_history)
        confidence_history = [max(0.1, 0.9 - (i * 0.1)) for i in range(count)]

    same_pattern = bool(context.approach_history and len(context.approach_history) > 1)

    result = foundation_check(
        iteration_count=context.rollout_index + 1,
        same_pattern=same_pattern,
        merge_ready=False,
        current_approach=context.current_approach,
        approach_history=context.approach_history,
        confidence=confidence,
        confidence_history=confidence_history,
    )

    if isinstance(result, str):
        if result.startswith("HALT"):
            decision = GovernanceDecision.HALT
            trigger = "iteration"
        elif result.startswith("WARN"):
            decision = GovernanceDecision.WARN
            trigger = "iteration"
        else:
            decision = GovernanceDecision.PASS
            trigger = "none"
        signals = {"iteration": context.rollout_index + 1}
        recommendation = result
        escalation_id = None
    else:
        decision = _to_decision(str(result.get("result", "PASS")))
        trigger = result.get("trigger", "none")
        signals = result.get("signals", {}) if isinstance(result.get("signals"), dict) else {}
        recommendation = result.get("recommendation", "")
        escalation_id = None

        if decision == GovernanceDecision.HALT:
            esc_result = handle_escalation(result, {"target_dir": context.target_dir})
            if isinstance(esc_result, dict):
                escalation_id = esc_result.get("escalation_id")

    return GovernanceResult(
        decision=decision,
        trigger=trigger,
        signals=signals,
        recommendation=recommendation,
        escalation_id=escalation_id,
        should_halt=(decision == GovernanceDecision.HALT),
    )
