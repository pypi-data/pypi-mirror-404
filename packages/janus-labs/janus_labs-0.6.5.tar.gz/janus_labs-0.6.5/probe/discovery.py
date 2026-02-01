"""DiscoveryPack generation for Probe layer."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Optional

from probe.explorer import ExplorationResult, ExplorationRun


@dataclass
class FailureCluster:
    """A cluster of similar failures."""
    cluster_id: str
    proposed_name: str
    frequency: int
    severity_hint: str
    exemplar_run_ids: list[str]
    common_mutation: Optional[str] = None
    description: str = ""


@dataclass
class DiscoveryPack:
    """
    Complete discovery output from Probe exploration.

    Contains failure clusters, metadata, and exemplar links.
    """
    pack_id: str
    timestamp: str
    task_explored: str
    failure_clusters: list[FailureCluster]
    metadata: dict
    total_runs: int
    novel_failures_found: int


def _cluster_by_exit_code(runs: list[ExplorationRun]) -> dict[str, list[ExplorationRun]]:
    """Group runs by exit code."""
    clusters: dict[str, list[ExplorationRun]] = {}
    for run in runs:
        code = run.bundle.get("exit_code", "unknown")
        if code not in clusters:
            clusters[code] = []
        clusters[code].append(run)
    return clusters


def _cluster_by_mutation(runs: list[ExplorationRun]) -> dict[str, list[ExplorationRun]]:
    """Group runs by mutation strategy."""
    clusters: dict[str, list[ExplorationRun]] = {}
    for run in runs:
        strategy = run.mutation.strategy.value
        if strategy not in clusters:
            clusters[strategy] = []
        clusters[strategy].append(run)
    return clusters


def _calculate_severity(runs: list[ExplorationRun]) -> str:
    """
    Calculate severity hint based on failure characteristics.

    - critical: crash or halt
    - high: failures with tool errors
    - medium: failures with no output
    - low: minor issues
    """
    for run in runs:
        if run.bundle.get("exit_code") in ("crash", "halt"):
            return "critical"
        if run.error:
            return "high"

    for run in runs:
        for trace in run.bundle.get("tool_traces", []):
            result = str(trace.get("result", ""))
            if "error" in result.lower():
                return "high"

    for run in runs:
        if not run.bundle.get("transcript"):
            return "medium"

    return "low"


def _generate_cluster_id(runs: list[ExplorationRun]) -> str:
    """Generate deterministic cluster ID."""
    content = json.dumps([run.run_id for run in runs], sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def _propose_cluster_name(
    runs: list[ExplorationRun],
    common_mutation: Optional[str],
) -> str:
    """Generate a proposed name for the cluster."""
    if not runs:
        return "unknown-cluster"

    exit_codes = {run.bundle.get("exit_code") for run in runs}

    if "crash" in exit_codes:
        return "crash-cluster"
    if "halt" in exit_codes:
        return "governance-halt-cluster"
    if "timeout" in exit_codes:
        return "timeout-cluster"

    if common_mutation == "tool_removal":
        return "tool-dependency-failure"
    if common_mutation == "context_reduce":
        return "context-sensitivity-failure"

    for run in runs:
        for trace in run.bundle.get("tool_traces", []):
            if "error" in str(trace.get("result", "")).lower():
                return "tool-error-cluster"

    return "unclassified-failure"


def generate_discovery_pack(
    exploration_result: ExplorationResult,
    task: str,
) -> DiscoveryPack:
    """
    Generate a DiscoveryPack from exploration results.

    Clusters failures by:
    1. Exit code (crash, halt, timeout, success)
    2. Mutation strategy that triggered failure
    3. Error patterns (via simple heuristics)

    In production with Phoenix, this would use embedding-based
    semantic clustering. For MVP, we use rule-based clustering.

    Args:
        exploration_result: Result from Explorer.explore()
        task: Original task explored

    Returns:
        DiscoveryPack with failure clusters
    """
    failed_runs = [run for run in exploration_result.runs if not run.success]

    for run in exploration_result.runs:
        if run.success:
            for trace in run.bundle.get("tool_traces", []):
                if "error" in str(trace.get("result", "")).lower():
                    if run not in failed_runs:
                        failed_runs.append(run)
                    break

    mutation_clusters = _cluster_by_mutation(failed_runs)

    failure_clusters: list[FailureCluster] = []
    for mutation, runs in mutation_clusters.items():
        if not runs:
            continue

        cluster = FailureCluster(
            cluster_id=_generate_cluster_id(runs),
            proposed_name=_propose_cluster_name(runs, mutation),
            frequency=len(runs),
            severity_hint=_calculate_severity(runs),
            exemplar_run_ids=[runs[0].run_id],
            common_mutation=mutation,
            description=f"Failures triggered by {mutation} mutation",
        )
        failure_clusters.append(cluster)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    failure_clusters.sort(key=lambda cluster: severity_order.get(cluster.severity_hint, 4))

    return DiscoveryPack(
        pack_id=hashlib.sha256(
            f"{task}-{exploration_result.total_runs}".encode()
        ).hexdigest()[:12],
        timestamp=datetime.now().isoformat(),
        task_explored=task,
        failure_clusters=failure_clusters,
        metadata={
            "total_runs": exploration_result.total_runs,
            "successful_runs": exploration_result.successful_runs,
            "failed_runs": exploration_result.failed_runs,
            "strategies_used": list(exploration_result.mutations_applied.keys()),
        },
        total_runs=exploration_result.total_runs,
        novel_failures_found=len(failure_clusters),
    )
