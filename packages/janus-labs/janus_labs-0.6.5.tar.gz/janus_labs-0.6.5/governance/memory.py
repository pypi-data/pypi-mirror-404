"""Persistence of governance decisions to Janus memory tiers."""

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import List, Optional


# Try mcp-janus memory module, fallback to local stubs for standalone operation
MCP_JANUS_PATH = Path(__file__).resolve().parents[2] / "mcp-janus"
if MCP_JANUS_PATH.exists() and str(MCP_JANUS_PATH) not in sys.path:
    sys.path.insert(0, str(MCP_JANUS_PATH))

try:
    from memory import read_tier, write_tier  # noqa: E402
except ImportError:
    from janus_types import read_tier, write_tier  # noqa: E402

from governance.bridge import GovernanceResult  # noqa: E402


def persist_governance_decision(
    result: GovernanceResult,
    behavior_id: str,
    rollout_index: int,
    target_dir: str = ".",
) -> bool:
    """
    Persist a governance decision to the governance memory tier.

    Args:
        result: GovernanceResult from check_governance()
        behavior_id: ID of the behavior being evaluated
        rollout_index: Index of the rollout
        target_dir: Directory containing .janus/

    Returns:
        True if persisted successfully
    """
    current = read_tier("governance", target_dir)
    if not isinstance(current, dict):
        current = {"schema_version": "1.0.0"}

    decisions = current.get("governance_decisions", [])
    if not isinstance(decisions, list):
        decisions = []

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "behavior_id": behavior_id,
        "rollout_index": rollout_index,
        "decision": result.decision.value,
        "trigger": result.trigger,
        "signals": result.signals,
        "escalation_id": result.escalation_id,
    }

    decisions.append(entry)

    if len(decisions) > 100:
        decisions = decisions[-100:]

    current["governance_decisions"] = decisions
    current["last_decision"] = entry

    success, _errors = write_tier("governance", current, target_dir)
    return success


def get_governance_history(
    behavior_id: Optional[str] = None,
    limit: int = 20,
    target_dir: str = ".",
) -> List[dict]:
    """
    Retrieve governance decision history.

    Args:
        behavior_id: Optional filter by behavior
        limit: Maximum entries to return
        target_dir: Directory containing .janus/

    Returns:
        List of governance decision entries (most recent first)
    """
    current = read_tier("governance", target_dir)
    if not isinstance(current, dict):
        return []

    decisions = current.get("governance_decisions", [])
    if not isinstance(decisions, list):
        return []

    if behavior_id:
        decisions = [d for d in decisions if d.get("behavior_id") == behavior_id]

    return list(reversed(decisions[-limit:]))


def get_halt_count(behavior_id: Optional[str] = None, target_dir: str = ".") -> int:
    """
    Count HALT decisions for governance statistics.

    Args:
        behavior_id: Optional filter by behavior
        target_dir: Directory containing .janus/

    Returns:
        Count of HALT decisions
    """
    history = get_governance_history(
        behavior_id=behavior_id,
        limit=100,
        target_dir=target_dir,
    )
    return sum(1 for entry in history if entry.get("decision") == "halt")
