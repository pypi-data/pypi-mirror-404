"""Suite runner for benchmark execution."""

from dataclasses import dataclass
import hashlib
from typing import Callable, Optional

from config.detection import ConfigMetadata
from gauge.governed_rollout import GovernedRolloutConfig, execute_governed_rollouts
from gauge.report import generate_benchmark_report, extract_governance_flags
from suite.definition import BenchmarkSuite
from suite.result import SuiteResult, generate_suite_result


@dataclass
class SuiteRunConfig:
    """Configuration for suite execution."""
    suite: BenchmarkSuite
    target_dir: str = "."
    seed: Optional[int] = 42
    config_metadata: Optional[ConfigMetadata] = None


def _coerce_score(value: float) -> tuple[float, float]:
    """
    Coerce a score into (score_0_1, score_0_100).

    Args:
        value: Raw score from execution output.

    Returns:
        Tuple of (0-1 score, 0-100 trust elasticity score).
    """
    if value <= 1.0:
        return value, value * 100.0
    if value <= 100.0:
        return value / 100.0, value
    return 1.0, 100.0


def _extract_score(output: dict) -> tuple[float, float]:
    if not isinstance(output, dict):
        return 0.0, 0.0
    if output.get("trust_elasticity") is not None:
        return _coerce_score(float(output["trust_elasticity"]))
    if output.get("score") is not None:
        return _coerce_score(float(output["score"]))
    return 0.0, 0.0


def run_suite(
    config: SuiteRunConfig,
    execute_fn: Callable[[int, str], dict],
) -> SuiteResult:
    """
    Execute all behaviors in a suite.

    1. For each behavior in suite.behaviors:
       a. Create GovernedRolloutConfig
       b. Execute rollouts via execute_governed_rollouts()
       c. Collect scores and governance results
    2. Aggregate into SuiteResult
    """
    config.suite.ensure_valid()

    behavior_reports = {}
    total_duration_ms = 0

    for behavior in config.suite.behaviors:
        rollout_config = GovernedRolloutConfig(
            behavior_id=behavior.behavior_id,
            max_rollouts=config.suite.rollouts_per_behavior,
            halt_on_governance=True,
            target_dir=config.target_dir,
        )

        def _execute(index: int):
            return execute_fn(index, behavior.behavior_id)

        rollouts = execute_governed_rollouts(rollout_config, _execute)
        governance_flags = extract_governance_flags(rollouts)

        scores_0_1 = []
        te_scores = []
        for run in rollouts:
            score_0_1, score_0_100 = _extract_score(run.execution_output)
            scores_0_1.append(score_0_1)
            te_scores.append(score_0_100)
            total_duration_ms += run.duration_ms

        report = generate_benchmark_report(
            behaviors=[behavior],
            behavior_scores={behavior.behavior_id: scores_0_1},
            trust_elasticity_scores={behavior.behavior_id: te_scores},
            config_fingerprint=_suite_fingerprint(config.suite, config.seed),
            governance_flags=governance_flags,
        )
        behavior_reports[behavior.behavior_id] = report

    return generate_suite_result(
        suite=config.suite,
        behavior_results=behavior_reports,
        config_fingerprint=_suite_fingerprint(config.suite, config.seed),
        duration_ms=total_duration_ms,
        config_metadata=config.config_metadata,
    )


def _suite_fingerprint(suite: BenchmarkSuite, seed: Optional[int]) -> str:
    content = f"{suite.comparability_key}:{seed}:{suite.judge_model}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
