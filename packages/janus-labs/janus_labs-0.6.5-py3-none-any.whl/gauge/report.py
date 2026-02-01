"""BenchmarkReport generation from DeepEval results."""

from dataclasses import dataclass
from datetime import datetime, timezone
import statistics
from typing import NotRequired, Optional, TypedDict
import uuid

from forge.behavior import BehaviorSpec
from gauge.governed_rollout import RolloutResult
from gauge.trust_elasticity import TrustElasticityMetric


class BehaviorResult(TypedDict):
    """Result for a single behavior across rollouts."""
    behavior_id: str
    name: str
    scores: list[float]
    mean_score: float
    std_dev: float
    pass_rate: float
    trust_elasticity: float
    grade: str


class AggregateMetrics(TypedDict):
    """Aggregate metrics across all behaviors."""
    trust_elasticity: float
    grade: str
    iterations_to_convergence: float
    foundation_check_rate: float
    halt_rate: float


class BenchmarkReport(TypedDict):
    """Complete benchmark report for a measurement run."""
    report_id: str
    timestamp: str
    behaviors: list[BehaviorResult]
    aggregate_metrics: AggregateMetrics
    config_fingerprint: str
    total_rollouts: int
    total_duration_ms: int
    governance: NotRequired["GovernanceSummary"]


class GovernanceSummary(TypedDict):
    """Governance summary attached to benchmark reports."""
    total_rollouts: int
    completed_rollouts: int
    halted_rollouts: int
    halt_rate: float
    triggers: dict
    escalation_ids: list[str]


@dataclass
class GovernanceFlags:
    """Governance flags for a benchmark report."""
    total_rollouts: int
    completed_rollouts: int
    halted_rollouts: int
    halt_rate: float
    triggers: dict
    escalation_ids: list[str]


def extract_governance_flags(
    rollout_results: list[RolloutResult],
) -> GovernanceFlags:
    """
    Extract governance flags from rollout results.

    Args:
        rollout_results: Results from execute_governed_rollouts()

    Returns:
        GovernanceFlags with aggregate statistics
    """
    total = len(rollout_results)
    completed = sum(1 for result in rollout_results if result.completed and not result.halted)
    halted = sum(1 for result in rollout_results if result.halted)

    triggers: dict = {}
    escalation_ids: list[str] = []

    for result in rollout_results:
        gov = result.governance_result
        if not gov:
            continue
        trigger = gov.trigger or "none"
        triggers[trigger] = triggers.get(trigger, 0) + 1
        if gov.escalation_id:
            escalation_ids.append(gov.escalation_id)

    return GovernanceFlags(
        total_rollouts=total,
        completed_rollouts=completed,
        halted_rollouts=halted,
        halt_rate=halted / total if total > 0 else 0.0,
        triggers=triggers,
        escalation_ids=escalation_ids,
    )


def calculate_behavior_result(
    behavior: BehaviorSpec,
    scores: list[float],
    trust_elasticity_scores: list[float],
) -> BehaviorResult:
    """
    Calculate result statistics for a single behavior.

    Args:
        behavior: The behavior specification
        scores: Raw scores from each rollout (0-1 scale)
        trust_elasticity_scores: Trust Elasticity scores (0-100)

    Returns:
        BehaviorResult with aggregated statistics
    """
    mean = statistics.mean(scores) if scores else 0.0
    std = statistics.stdev(scores) if len(scores) > 1 else 0.0
    pass_count = sum(1 for score in scores if score >= behavior.threshold / 10.0)
    pass_rate = pass_count / len(scores) if scores else 0.0

    te_mean = statistics.mean(trust_elasticity_scores) if trust_elasticity_scores else 0.0

    return BehaviorResult(
        behavior_id=behavior.behavior_id,
        name=behavior.name,
        scores=scores,
        mean_score=mean,
        std_dev=std,
        pass_rate=pass_rate,
        trust_elasticity=te_mean,
        grade=TrustElasticityMetric.score_to_grade(te_mean),
    )


def generate_benchmark_report(
    behaviors: list[BehaviorSpec],
    behavior_scores: dict[str, list[float]],
    trust_elasticity_scores: dict[str, list[float]],
    config_fingerprint: str,
    foundation_checks: int = 0,
    halts: int = 0,
    total_iterations: int = 1,
    duration_ms: int = 0,
    governance_flags: Optional[GovernanceFlags] = None,
) -> BenchmarkReport:
    """
    Generate a complete BenchmarkReport.

    Args:
        behaviors: List of measured behaviors
        behavior_scores: Map of behavior_id -> scores
        trust_elasticity_scores: Map of behavior_id -> TE scores
        config_fingerprint: SHA256 of agent config
        foundation_checks: Total foundation checks triggered
        halts: Total halted runs
        total_iterations: Total iterations across all rollouts
        duration_ms: Total measurement duration

    Returns:
        Complete BenchmarkReport
    """
    behavior_results: list[BehaviorResult] = []
    all_te_scores: list[float] = []
    total_rollouts = 0

    for behavior in behaviors:
        bid = behavior.behavior_id
        scores = behavior_scores.get(bid, [])
        te_scores = trust_elasticity_scores.get(bid, [])

        result = calculate_behavior_result(behavior, scores, te_scores)
        behavior_results.append(result)
        all_te_scores.extend(te_scores)
        total_rollouts += len(scores)

    aggregate_te = statistics.mean(all_te_scores) if all_te_scores else 0.0

    report = BenchmarkReport(
        report_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        behaviors=behavior_results,
        aggregate_metrics=AggregateMetrics(
            trust_elasticity=aggregate_te,
            grade=TrustElasticityMetric.score_to_grade(aggregate_te),
            iterations_to_convergence=total_iterations / max(1, total_rollouts),
            foundation_check_rate=foundation_checks / max(1, total_rollouts),
            halt_rate=halts / max(1, total_rollouts),
        ),
        config_fingerprint=config_fingerprint,
        total_rollouts=total_rollouts,
        total_duration_ms=duration_ms,
    )

    if governance_flags:
        report["governance"] = GovernanceSummary(
            total_rollouts=governance_flags.total_rollouts,
            completed_rollouts=governance_flags.completed_rollouts,
            halted_rollouts=governance_flags.halted_rollouts,
            halt_rate=governance_flags.halt_rate,
            triggers=governance_flags.triggers,
            escalation_ids=governance_flags.escalation_ids,
        )

    return report
