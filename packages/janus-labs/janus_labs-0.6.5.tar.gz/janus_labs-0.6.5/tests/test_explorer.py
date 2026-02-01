"""Tests for exploration runner."""

from probe.explorer import Explorer, ExplorationConfig
from probe.mutations import MutationStrategy


def test_explorer_runs():
    """Explorer executes configured runs."""
    config = ExplorationConfig(
        max_runs=6,
        strategies=[MutationStrategy.NONE, MutationStrategy.TASK_VARIATION],
    )
    explorer = Explorer(config)

    result = explorer.explore("Fix the bug")

    assert result.total_runs == 6
    assert len(explorer.get_traces()) == 6


def test_explorer_tracks_mutations():
    """Explorer tracks which mutations were applied."""
    config = ExplorationConfig(
        max_runs=4,
        strategies=[MutationStrategy.NONE, MutationStrategy.TASK_VARIATION],
    )
    explorer = Explorer(config)

    result = explorer.explore("Test task")

    assert "none" in result.mutations_applied
    assert "task_variation" in result.mutations_applied
