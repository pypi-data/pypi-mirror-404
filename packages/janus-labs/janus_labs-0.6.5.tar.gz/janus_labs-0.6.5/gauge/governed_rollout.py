"""Rollout executor with integrated Janus governance."""

from dataclasses import dataclass
import time
from typing import Any, Callable, List, Optional

from governance.bridge import GovernanceContext, GovernanceResult, check_governance


@dataclass
class RolloutResult:
    """Result of a governed rollout."""
    rollout_index: int
    completed: bool
    halted: bool
    governance_result: Optional[GovernanceResult]
    execution_output: Any
    duration_ms: int


@dataclass
class GovernedRolloutConfig:
    """Configuration for governed rollout execution."""
    behavior_id: str
    max_rollouts: int = 10
    halt_on_governance: bool = True
    target_dir: str = "."


def execute_governed_rollouts(
    config: GovernedRolloutConfig,
    execute_fn: Callable[[int], Any],
    extract_approach_fn: Optional[Callable[[Any], str]] = None,
    extract_reasoning_fn: Optional[Callable[[Any], str]] = None,
) -> List[RolloutResult]:
    """
    Execute rollouts with governance checks at each iteration.

    Args:
        config: Rollout configuration
        execute_fn: Function that executes a single rollout given index
        extract_approach_fn: Optional function to extract approach from output
        extract_reasoning_fn: Optional function to extract reasoning from output

    Returns:
        List of RolloutResult for each rollout (may be < max_rollouts if halted)
    """
    results: List[RolloutResult] = []
    approach_history: List[str] = []

    for i in range(config.max_rollouts):
        start_time = time.perf_counter()
        completed = True
        output: Any

        try:
            output = execute_fn(i)
        except Exception as exc:
            output = {"error": str(exc)}
            completed = False

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        current_approach = None
        if extract_approach_fn and output is not None:
            try:
                current_approach = extract_approach_fn(output)
            except Exception:
                current_approach = None

        reasoning_text = None
        if extract_reasoning_fn and output is not None:
            try:
                reasoning_text = extract_reasoning_fn(output)
            except Exception:
                reasoning_text = None

        context = GovernanceContext(
            rollout_index=i,
            behavior_id=config.behavior_id,
            current_approach=current_approach,
            approach_history=approach_history.copy() if approach_history else None,
            reasoning_text=reasoning_text,
            target_dir=config.target_dir,
        )

        gov_result = check_governance(context)

        if current_approach:
            approach_history.append(current_approach)
            if len(approach_history) > 5:
                approach_history = approach_history[-5:]

        result = RolloutResult(
            rollout_index=i,
            completed=completed,
            halted=gov_result.should_halt,
            governance_result=gov_result,
            execution_output=output,
            duration_ms=duration_ms,
        )
        results.append(result)

        if gov_result.should_halt and config.halt_on_governance:
            break

    return results
