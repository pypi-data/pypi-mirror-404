"""Threshold configuration for regression gating."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import yaml

from suite.registry import get_suite


@dataclass
class BehaviorThreshold:
    """Threshold configuration for a single behavior."""
    behavior_id: str
    max_regression_pct: float = 5.0
    min_score: Optional[float] = None
    required: bool = True


@dataclass
class ThresholdConfig:
    """Suite-level threshold configuration."""
    suite_id: str
    default_max_regression_pct: float = 5.0
    default_min_score: Optional[float] = None
    behaviors: Dict[str, BehaviorThreshold] = field(default_factory=dict)
    fail_on_any_halt: bool = True


def load_thresholds(path: str) -> ThresholdConfig:
    """Load threshold config from YAML file."""
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    suite_id = payload.get("suite_id")
    if not suite_id:
        raise ValueError("threshold config missing suite_id")

    default_max = float(payload.get("default_max_regression_pct", 5.0))
    default_min = payload.get("default_min_score", None)
    default_min_score = float(default_min) if default_min is not None else None
    fail_on_any_halt = bool(payload.get("fail_on_any_halt", True))

    behaviors: Dict[str, BehaviorThreshold] = {}
    for behavior_id, data in (payload.get("behaviors") or {}).items():
        max_regression_pct = float(data.get("max_regression_pct", default_max))
        min_score_raw = data.get("min_score", default_min_score)
        min_score = float(min_score_raw) if min_score_raw is not None else None
        required = bool(data.get("required", True))
        behaviors[behavior_id] = BehaviorThreshold(
            behavior_id=behavior_id,
            max_regression_pct=max_regression_pct,
            min_score=min_score,
            required=required,
        )

    return ThresholdConfig(
        suite_id=suite_id,
        default_max_regression_pct=default_max,
        default_min_score=default_min_score,
        behaviors=behaviors,
        fail_on_any_halt=fail_on_any_halt,
    )


def default_thresholds(suite_id: str) -> ThresholdConfig:
    """Return default thresholds for a suite."""
    suite = get_suite(suite_id)
    config = ThresholdConfig(suite_id=suite_id)
    if suite is None:
        return config

    for behavior in suite.behaviors:
        config.behaviors[behavior.behavior_id] = BehaviorThreshold(
            behavior_id=behavior.behavior_id,
            max_regression_pct=config.default_max_regression_pct,
            min_score=config.default_min_score,
            required=True,
        )

    return config
