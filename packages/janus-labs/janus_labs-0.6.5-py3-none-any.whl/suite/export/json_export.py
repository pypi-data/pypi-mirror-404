"""JSON export and load for SuiteResult."""

import json
from pathlib import Path

from config.detection import ConfigMetadata
from suite.result import BehaviorScore, GovernanceFlags, SuiteResult


def export_json(result: SuiteResult, output_path: str) -> str:
    """
    Export SuiteResult to JSON.

    Returns:
        Path to generated JSON file
    """
    output = Path(output_path)
    payload = {
        "suite_id": result.suite_id,
        "suite_version": result.suite_version,
        "config_fingerprint": result.config_fingerprint,
        "timestamp": result.timestamp,
        "headline_score": result.headline_score,
        "grade": result.grade,
        "behavior_scores": [score.__dict__ for score in result.behavior_scores],
        "governance_flags": result.governance_flags.__dict__,
        "comparability_key": result.comparability_key,
        "total_rollouts": result.total_rollouts,
        "total_duration_ms": result.total_duration_ms,
    }
    if result.config_metadata:
        payload["config_metadata"] = {
            "config_source": result.config_metadata.config_source,
            "config_hash": result.config_metadata.config_hash,
            "config_files": result.config_metadata.config_files,
            "captured_at": result.config_metadata.captured_at,
        }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output)


def load_json(path: str) -> SuiteResult:
    """Load SuiteResult from JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    behavior_scores = [
        BehaviorScore(**item) for item in data.get("behavior_scores", [])
    ]
    governance_flags = GovernanceFlags(**data["governance_flags"])
    config_metadata = None
    if "config_metadata" in data and data["config_metadata"] is not None:
        config_metadata = ConfigMetadata(**data["config_metadata"])
    return SuiteResult(
        suite_id=data["suite_id"],
        suite_version=data["suite_version"],
        config_fingerprint=data["config_fingerprint"],
        timestamp=data["timestamp"],
        headline_score=data["headline_score"],
        grade=data["grade"],
        behavior_scores=behavior_scores,
        governance_flags=governance_flags,
        comparability_key=data["comparability_key"],
        total_rollouts=data["total_rollouts"],
        total_duration_ms=data["total_duration_ms"],
        config_metadata=config_metadata,
    )
