"""Tests for DiscoveryPack generation."""

from probe.discovery import generate_discovery_pack, _calculate_severity
from probe.explorer import Explorer, ExplorationConfig


def test_discovery_pack_generation():
    """DiscoveryPack generated from exploration."""
    config = ExplorationConfig(max_runs=6)
    explorer = Explorer(config)
    result = explorer.explore("Fix the bug")

    pack = generate_discovery_pack(result, "Fix the bug")

    assert pack.pack_id is not None
    assert pack.total_runs == 6
    assert pack.task_explored == "Fix the bug"


def test_severity_calculation():
    """Severity calculation helper is callable."""
    assert callable(_calculate_severity)
