"""Mutation strategies for Probe exploration."""

from dataclasses import dataclass
from enum import Enum
import random


class MutationStrategy(Enum):
    """Available mutation strategies."""
    TASK_VARIATION = "task_variation"
    TOOL_REMOVAL = "tool_removal"
    CONSTRAINT_ADDITION = "constraint_add"
    CONTEXT_REDUCTION = "context_reduce"
    NONE = "none"


@dataclass
class TaskMutation:
    """A mutation applied to a task."""
    strategy: MutationStrategy
    original_task: str
    mutated_task: str
    mutation_details: dict


def _vary_task(task: str, seed: int | None = None) -> TaskMutation:
    """
    Rephrase a task while preserving intent.

    Simple implementation: add prefixes/suffixes that
    change framing but not core request.
    """
    if seed is not None:
        random.seed(seed)

    variations = [
        f"Please {task.lower()}",
        f"I need you to {task.lower()}",
        f"Can you {task.lower()}?",
        f"{task} Make sure to be thorough.",
        f"{task} Do this quickly.",
        f"Urgently: {task}",
    ]

    mutated = random.choice(variations)

    return TaskMutation(
        strategy=MutationStrategy.TASK_VARIATION,
        original_task=task,
        mutated_task=mutated,
        mutation_details={"variation_type": "rephrasing"},
    )


def _remove_tool(
    task: str,
    available_tools: list[str],
    seed: int | None = None,
) -> TaskMutation:
    """
    Create a mutation that simulates tool removal.

    Adds constraint to task indicating tool unavailability.
    """
    if seed is not None:
        random.seed(seed)

    if not available_tools:
        return TaskMutation(
            strategy=MutationStrategy.TOOL_REMOVAL,
            original_task=task,
            mutated_task=task,
            mutation_details={"removed_tool": None, "reason": "no tools available"},
        )

    tool_to_remove = random.choice(available_tools)
    mutated = f"{task} (Note: The {tool_to_remove} tool is unavailable)"

    return TaskMutation(
        strategy=MutationStrategy.TOOL_REMOVAL,
        original_task=task,
        mutated_task=mutated,
        mutation_details={"removed_tool": tool_to_remove},
    )


def _add_constraint(task: str, seed: int | None = None) -> TaskMutation:
    """Add a constraint to the task."""
    if seed is not None:
        random.seed(seed)

    constraints = [
        "Do not modify any test files.",
        "Only make changes to Python files.",
        "Explain each step before executing.",
        "Use only built-in libraries.",
        "Complete this in under 5 tool calls.",
    ]

    constraint = random.choice(constraints)
    mutated = f"{task} Constraint: {constraint}"

    return TaskMutation(
        strategy=MutationStrategy.CONSTRAINT_ADDITION,
        original_task=task,
        mutated_task=mutated,
        mutation_details={"added_constraint": constraint},
    )


def _reduce_context(task: str, seed: int | None = None) -> TaskMutation:
    """
    Reduce context provided in the task.

    Simple implementation: truncate or remove details.
    """
    _ = seed
    sentences = task.split(". ")
    if len(sentences) > 1:
        mutated = sentences[0] + "."
    else:
        mutated = task[:50] + "..." if len(task) > 50 else task

    return TaskMutation(
        strategy=MutationStrategy.CONTEXT_REDUCTION,
        original_task=task,
        mutated_task=mutated,
        mutation_details={"reduction_type": "truncation"},
    )


def apply_mutation(
    task: str,
    strategy: MutationStrategy,
    available_tools: list[str] | None = None,
    seed: int | None = None,
) -> TaskMutation:
    """
    Apply a mutation strategy to a task.

    Args:
        task: Original task description
        strategy: Mutation strategy to apply
        available_tools: List of tools (for TOOL_REMOVAL)
        seed: Random seed for reproducibility

    Returns:
        TaskMutation with mutated task
    """
    if strategy == MutationStrategy.NONE:
        return TaskMutation(
            strategy=MutationStrategy.NONE,
            original_task=task,
            mutated_task=task,
            mutation_details={},
        )
    if strategy == MutationStrategy.TASK_VARIATION:
        return _vary_task(task, seed)
    if strategy == MutationStrategy.TOOL_REMOVAL:
        return _remove_tool(task, available_tools or [], seed)
    if strategy == MutationStrategy.CONSTRAINT_ADDITION:
        return _add_constraint(task, seed)
    if strategy == MutationStrategy.CONTEXT_REDUCTION:
        return _reduce_context(task, seed)
    raise ValueError(f"Unknown mutation strategy: {strategy}")


def generate_mutation_suite(
    task: str,
    strategies: list[MutationStrategy] | None = None,
    available_tools: list[str] | None = None,
    seed: int | None = None,
) -> list[TaskMutation]:
    """
    Generate a suite of mutations for a task.

    Args:
        task: Original task
        strategies: Strategies to apply (default: all)
        available_tools: Available tools list
        seed: Base seed for reproducibility

    Returns:
        List of TaskMutation objects
    """
    if strategies is None:
        strategies = list(MutationStrategy)

    mutations = []
    for i, strategy in enumerate(strategies):
        mutation_seed = seed + i if seed is not None else None
        mutations.append(
            apply_mutation(task, strategy, available_tools, mutation_seed)
        )

    return mutations
