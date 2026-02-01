"""Comparison logic for regression gating."""

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import json
from pathlib import Path
from typing import List, Optional

from suite.result import SuiteResult
from suite.thresholds import BehaviorThreshold, ThresholdConfig


class ComparisonVerdict(Enum):
    PASS = "pass"
    REGRESSION = "regression"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class BehaviorComparison:
    """Comparison result for a single behavior."""
    behavior_id: str
    name: str
    baseline_score: float
    current_score: float
    delta: float
    delta_pct: float
    threshold_pct: float
    min_score: Optional[float]
    verdict: ComparisonVerdict
    message: str


@dataclass
class ComparisonResult:
    """Complete comparison result."""
    suite_id: str
    suite_version: str
    comparability_key: str
    verdict: ComparisonVerdict
    headline_baseline: float
    headline_current: float
    headline_delta_pct: float
    behavior_comparisons: List[BehaviorComparison]
    baseline_halts: int
    current_halts: int
    new_halts: List[str]
    regressions: int
    warnings: int
    passes: int
    exit_code: int
    ci_message: str


def _resolve_threshold(config: ThresholdConfig, behavior_id: str) -> BehaviorThreshold:
    override = config.behaviors.get(behavior_id)
    if override:
        return override
    return BehaviorThreshold(
        behavior_id=behavior_id,
        max_regression_pct=config.default_max_regression_pct,
        min_score=config.default_min_score,
        required=True,
    )


def _calculate_delta_pct(baseline_score: float, current_score: float) -> float:
    if baseline_score <= 0:
        return 0.0
    return ((current_score - baseline_score) / baseline_score) * 100.0


def compare_results(
    baseline: SuiteResult,
    current: SuiteResult,
    config: ThresholdConfig,
) -> ComparisonResult:
    """Compare two suite results with threshold configuration."""
    if baseline.comparability_key != current.comparability_key:
        return ComparisonResult(
            suite_id=baseline.suite_id,
            suite_version=baseline.suite_version,
            comparability_key=baseline.comparability_key,
            verdict=ComparisonVerdict.ERROR,
            headline_baseline=baseline.headline_score,
            headline_current=current.headline_score,
            headline_delta_pct=0.0,
            behavior_comparisons=[],
            baseline_halts=baseline.governance_flags.halted_count,
            current_halts=current.governance_flags.halted_count,
            new_halts=[],
            regressions=0,
            warnings=0,
            passes=0,
            exit_code=2,
            ci_message="Comparability key mismatch.",
        )

    baseline_map = {score.behavior_id: score for score in baseline.behavior_scores}
    current_map = {score.behavior_id: score for score in current.behavior_scores}
    behavior_ids = sorted(set(baseline_map) | set(current_map))

    behavior_comparisons: List[BehaviorComparison] = []
    regressions = 0
    warnings = 0
    passes = 0

    for behavior_id in behavior_ids:
        threshold = _resolve_threshold(config, behavior_id)
        baseline_score_obj = baseline_map.get(behavior_id)
        current_score_obj = current_map.get(behavior_id)
        name = (
            (current_score_obj.name if current_score_obj else None)
            or (baseline_score_obj.name if baseline_score_obj else None)
            or behavior_id
        )

        if baseline_score_obj is None or current_score_obj is None:
            message = "Missing baseline or current behavior result."
            verdict = ComparisonVerdict.ERROR if threshold.required else ComparisonVerdict.WARNING
            behavior_comparisons.append(
                BehaviorComparison(
                    behavior_id=behavior_id,
                    name=name,
                    baseline_score=baseline_score_obj.score if baseline_score_obj else 0.0,
                    current_score=current_score_obj.score if current_score_obj else 0.0,
                    delta=0.0,
                    delta_pct=0.0,
                    threshold_pct=threshold.max_regression_pct,
                    min_score=threshold.min_score,
                    verdict=verdict,
                    message=message,
                )
            )
            if verdict == ComparisonVerdict.ERROR:
                regressions += 1
            elif verdict == ComparisonVerdict.WARNING:
                warnings += 1
            else:
                passes += 1
            continue

        baseline_score = float(baseline_score_obj.score)
        current_score = float(current_score_obj.score)
        delta = current_score - baseline_score
        delta_pct = _calculate_delta_pct(baseline_score, current_score)

        failures = []
        if threshold.min_score is not None and current_score < threshold.min_score:
            failures.append(
                f"score {current_score:.1f} below min {threshold.min_score:.1f}"
            )
        if delta_pct < 0 and abs(delta_pct) >= threshold.max_regression_pct:
            failures.append(
                f"drop {abs(delta_pct):.1f}% exceeds {threshold.max_regression_pct:.1f}%"
            )

        if failures:
            verdict = ComparisonVerdict.REGRESSION if threshold.required else ComparisonVerdict.WARNING
            message = "; ".join(failures)
        else:
            verdict = ComparisonVerdict.PASS
            message = "within thresholds"

        behavior_comparisons.append(
            BehaviorComparison(
                behavior_id=behavior_id,
                name=name,
                baseline_score=baseline_score,
                current_score=current_score,
                delta=delta,
                delta_pct=delta_pct,
                threshold_pct=threshold.max_regression_pct,
                min_score=threshold.min_score,
                verdict=verdict,
                message=message,
            )
        )

        if verdict == ComparisonVerdict.PASS:
            passes += 1
        elif verdict == ComparisonVerdict.WARNING:
            warnings += 1
        else:
            regressions += 1

    baseline_halts = baseline.governance_flags.halted_count
    current_halts = current.governance_flags.halted_count
    baseline_halted = set(baseline.governance_flags.halted_behaviors)
    current_halted = set(current.governance_flags.halted_behaviors)
    new_halts = sorted(current_halted - baseline_halted)

    if config.fail_on_any_halt and new_halts:
        regressions += len(new_halts)

    headline_delta_pct = _calculate_delta_pct(
        baseline.headline_score, current.headline_score
    )

    verdict = ComparisonVerdict.PASS
    exit_code = 0

    if regressions > 0:
        verdict = ComparisonVerdict.REGRESSION
        exit_code = 1
    elif warnings > 0 or (new_halts and not config.fail_on_any_halt):
        verdict = ComparisonVerdict.WARNING
        exit_code = 0

    if any(comp.verdict == ComparisonVerdict.ERROR for comp in behavior_comparisons):
        verdict = ComparisonVerdict.ERROR
        exit_code = 2

    ci_message = (
        f"{verdict.value.upper()}: "
        f"{regressions} regressions, {warnings} warnings, "
        f"headline {current.headline_score:.1f} ({headline_delta_pct:+.1f}%)"
    )

    return ComparisonResult(
        suite_id=baseline.suite_id,
        suite_version=baseline.suite_version,
        comparability_key=baseline.comparability_key,
        verdict=verdict,
        headline_baseline=baseline.headline_score,
        headline_current=current.headline_score,
        headline_delta_pct=headline_delta_pct,
        behavior_comparisons=behavior_comparisons,
        baseline_halts=baseline_halts,
        current_halts=current_halts,
        new_halts=new_halts,
        regressions=regressions,
        warnings=warnings,
        passes=passes,
        exit_code=exit_code,
        ci_message=ci_message,
    )


def comparison_to_dict(result: ComparisonResult) -> dict:
    """Convert ComparisonResult to JSON-serializable dict."""
    def _convert(value):
        if isinstance(value, Enum):
            return value.value
        if is_dataclass(value):
            return {k: _convert(v) for k, v in asdict(value).items()}
        if isinstance(value, list):
            return [_convert(v) for v in value]
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        return value

    return _convert(result)


def export_comparison_json(result: ComparisonResult, output_path: str) -> str:
    """Export ComparisonResult to JSON file."""
    payload = comparison_to_dict(result)
    output = Path(output_path)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output)


def print_comparison_text(result: ComparisonResult) -> None:
    """Print human-readable comparison summary."""
    print(result.ci_message)
    for comparison in result.behavior_comparisons:
        verdict = comparison.verdict.value.upper()
        print(
            f"- {comparison.behavior_id} {verdict}: "
            f"{comparison.baseline_score:.1f} -> {comparison.current_score:.1f} "
            f"({comparison.delta_pct:+.1f}%)"
        )
