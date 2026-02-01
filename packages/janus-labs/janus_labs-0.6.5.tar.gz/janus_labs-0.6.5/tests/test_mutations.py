"""Tests for mutation strategies."""

from probe.mutations import (
    MutationStrategy,
    apply_mutation,
    generate_mutation_suite,
)


def test_task_variation():
    """Task variation changes phrasing."""
    mutation = apply_mutation(
        "Fix the bug",
        MutationStrategy.TASK_VARIATION,
        seed=42,
    )
    assert mutation.mutated_task != mutation.original_task
    assert mutation.strategy == MutationStrategy.TASK_VARIATION


def test_tool_removal():
    """Tool removal adds constraint."""
    mutation = apply_mutation(
        "Fix the bug",
        MutationStrategy.TOOL_REMOVAL,
        available_tools=["read_file", "write_file"],
        seed=42,
    )
    assert "unavailable" in mutation.mutated_task.lower()
    assert mutation.mutation_details.get("removed_tool") is not None


def test_mutation_suite():
    """Suite generates all mutation types."""
    mutations = generate_mutation_suite("Fix the bug", seed=42)
    strategies = {mutation.strategy for mutation in mutations}
    assert MutationStrategy.TASK_VARIATION in strategies
    assert MutationStrategy.NONE in strategies


def test_seed_reproducibility():
    """Same seed produces same mutation."""
    m1 = apply_mutation("Fix bug", MutationStrategy.TASK_VARIATION, seed=123)
    m2 = apply_mutation("Fix bug", MutationStrategy.TASK_VARIATION, seed=123)
    assert m1.mutated_task == m2.mutated_task
