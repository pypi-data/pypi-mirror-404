"""SuiteResult generation for benchmark suite runs.

JL-210.1: Score Status Field - distinguishes judged vs unjudged outcomes.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from config.detection import ConfigMetadata
from gauge.report import BenchmarkReport
from gauge.trust_elasticity import TrustElasticityMetric
from suite.definition import BenchmarkSuite


class BehaviorStatus(str, Enum):
    """Status of behavior scoring.

    JL-210.1: Distinguishes judged vs unjudged outcomes.
    """
    PASSED = "PASSED"       # Judged and met threshold
    FAILED = "FAILED"       # Judged but did not meet threshold
    JUDGE_FAILED = "JUDGE_FAILED"  # Could not be judged (rate limit, error)
    SKIPPED = "SKIPPED"     # Intentionally skipped
    PENDING = "PENDING"     # Not yet processed


@dataclass
class BehaviorScore:
    """Score for a single behavior in a suite."""
    behavior_id: str
    name: str
    score: Optional[float]  # None when status is JUDGE_FAILED/SKIPPED
    trust_elasticity: Optional[float]  # None when status is JUDGE_FAILED/SKIPPED
    grade: str
    passed: bool
    halted: bool
    status: BehaviorStatus = BehaviorStatus.PASSED  # Default for backwards compat
    error: Optional[str] = None  # Error message when JUDGE_FAILED


@dataclass
class GovernanceFlags:
    """Suite-level governance summary."""
    any_halted: bool
    halted_count: int
    halted_behaviors: List[str]
    foundation_check_rate: float


@dataclass
class SuiteResult:
    """Complete result of a benchmark suite run."""
    suite_id: str
    suite_version: str
    config_fingerprint: str
    timestamp: str
    headline_score: float
    grade: str
    behavior_scores: List[BehaviorScore]
    governance_flags: GovernanceFlags
    comparability_key: str
    total_rollouts: int
    total_duration_ms: int
    config_metadata: Optional[ConfigMetadata] = None


def _calculate_foundation_check_rate(reports: List[BenchmarkReport]) -> float:
    total_rollouts = 0
    total_checks = 0.0
    for report in reports:
        rollouts = report.get("total_rollouts", 0)
        rate = report.get("aggregate_metrics", {}).get("foundation_check_rate", 0.0)
        total_rollouts += rollouts
        total_checks += rate * rollouts
    if total_rollouts == 0:
        return 0.0
    return total_checks / total_rollouts


def _safe_behavior_result(report: BenchmarkReport) -> dict:
    behaviors = report.get("behaviors", [])
    return behaviors[0] if behaviors else {}


def generate_suite_result(
    suite: BenchmarkSuite,
    behavior_results: Dict[str, BenchmarkReport],
    config_fingerprint: str,
    duration_ms: int,
    config_metadata: Optional[ConfigMetadata] = None,
) -> SuiteResult:
    """Generate SuiteResult from individual behavior reports."""
    behavior_scores: List[BehaviorScore] = []
    trust_elasticities: List[float] = []
    halted_behaviors: List[str] = []
    total_rollouts = 0

    for behavior in suite.behaviors:
        report = behavior_results.get(behavior.behavior_id)
        if not report:
            continue

        total_rollouts += report.get("total_rollouts", 0)
        result = _safe_behavior_result(report)
        trust_elasticity = float(result.get("trust_elasticity", 0.0))
        trust_elasticities.append(trust_elasticity)
        mean_score = float(result.get("mean_score", 0.0))
        passed = mean_score >= (behavior.threshold / 10.0)

        governance = report.get("governance", {})
        halted = bool(governance.get("halted_rollouts", 0))
        if halted:
            halted_behaviors.append(behavior.behavior_id)

        # Determine behavior status based on score result
        judge_status = result.get("status", "OK")
        if judge_status in ("RATE_LIMITED", "CIRCUIT_OPEN", "ERROR"):
            status = BehaviorStatus.JUDGE_FAILED
            error_msg = result.get("error")
        elif passed:
            status = BehaviorStatus.PASSED
            error_msg = None
        else:
            status = BehaviorStatus.FAILED
            error_msg = None

        behavior_scores.append(
            BehaviorScore(
                behavior_id=behavior.behavior_id,
                name=behavior.name,
                score=trust_elasticity if status != BehaviorStatus.JUDGE_FAILED else None,
                trust_elasticity=trust_elasticity if status != BehaviorStatus.JUDGE_FAILED else None,
                grade=result.get("grade", TrustElasticityMetric.score_to_grade(trust_elasticity)) if status != BehaviorStatus.JUDGE_FAILED else "?",
                passed=passed,
                halted=halted,
                status=status,
                error=error_msg,
            )
        )

    # Calculate headline excluding JUDGE_FAILED behaviors (JL-210.1)
    judged_scores = [b for b in behavior_scores if b.status in (BehaviorStatus.PASSED, BehaviorStatus.FAILED)]
    if judged_scores:
        headline = sum(b.trust_elasticity for b in judged_scores if b.trust_elasticity is not None) / len(judged_scores)
    else:
        headline = 0.0  # All behaviors failed to judge
    grade = TrustElasticityMetric.score_to_grade(headline)
    governance_flags = GovernanceFlags(
        any_halted=bool(halted_behaviors),
        halted_count=len(halted_behaviors),
        halted_behaviors=halted_behaviors,
        foundation_check_rate=_calculate_foundation_check_rate(list(behavior_results.values())),
    )

    return SuiteResult(
        suite_id=suite.suite_id,
        suite_version=suite.version,
        config_fingerprint=config_fingerprint,
        timestamp=datetime.now(timezone.utc).isoformat(),
        headline_score=headline,
        grade=grade,
        behavior_scores=behavior_scores,
        governance_flags=governance_flags,
        comparability_key=suite.comparability_key,
        total_rollouts=total_rollouts,
        total_duration_ms=duration_ms,
        config_metadata=config_metadata,
    )
