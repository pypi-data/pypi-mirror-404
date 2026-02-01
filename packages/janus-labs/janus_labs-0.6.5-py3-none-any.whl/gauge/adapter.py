"""Adapter to convert BehaviorSpec to DeepEval test cases.

E8-S4: Enhanced with qualitative rubric support for multi-dimensional scoring.
"""

from typing import Optional

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from forge.behavior import BehaviorSpec
from harness.types import RunArtifactBundle
from gauge.qualitative import QualitativeRubric


def behavior_to_test_case(
    behavior: BehaviorSpec,
    bundle: RunArtifactBundle,
    qualitative_rubric: Optional[QualitativeRubric] = None,
) -> LLMTestCase:
    """
    Convert a BehaviorSpec + RunArtifactBundle to a DeepEval LLMTestCase.

    Args:
        behavior: The behavior specification with rubric
        bundle: The captured agent execution artifacts
        qualitative_rubric: Optional qualitative rubric for enhanced evaluation

    Returns:
        LLMTestCase ready for DeepEval evaluation
    """
    transcript_text = "\n".join(
        f"[{msg['role']}]: {msg['content']}"
        for msg in bundle["transcript"]
    )

    tool_summary = "\n".join(
        f"- {trace['tool_name']}({trace['arguments']}) -> {trace['result']}"
        for trace in bundle["tool_traces"]
    )

    # Include git diff for code quality evaluation
    diff_text = bundle.get("repo_diff", {}).get("patch", "No diff available")

    # Include test results for outcome evaluation
    test_results = bundle.get("test_results", {})
    test_summary = (
        f"Tests: {test_results.get('passed', 0)} passed, "
        f"{test_results.get('failed', 0)} failed"
    )

    # Build context with rubric
    if qualitative_rubric:
        context = [qualitative_rubric.get_full_evaluation_prompt()]
    else:
        context = [behavior.get_rubric_prompt()]

    return LLMTestCase(
        input=f"Behavior: {behavior.name}\n\nTask transcript:\n{transcript_text}",
        actual_output=(
            f"Tool usage:\n{tool_summary}\n\n"
            f"Code changes:\n{diff_text}\n\n"
            f"{test_summary}\n\n"
            f"Exit: {bundle['exit_code']}"
        ),
        expected_output=behavior.description,
        context=context,
    )


def create_geval_metric(
    behavior: BehaviorSpec,
    qualitative_rubric: Optional[QualitativeRubric] = None,
    model: Optional[str] = None,
) -> GEval:
    """
    Create a GEval metric configured for this behavior's rubric.

    Args:
        behavior: The behavior specification
        qualitative_rubric: Optional qualitative rubric for detailed evaluation
        model: LLM model string (e.g., "gpt-4o-mini") - must be passed at construction

    Returns:
        Configured GEval metric for scoring
    """
    if qualitative_rubric:
        # Use detailed evaluation steps from qualitative rubric
        evaluation_steps = qualitative_rubric.get_evaluation_steps()
        criteria = qualitative_rubric.get_full_evaluation_prompt()
    else:
        # Basic evaluation steps
        evaluation_steps = [
            f"Review the agent's behavior against: {behavior.description}",
            "Apply the rubric from the context to score 1-10",
            f"Minimum acceptable score is {behavior.threshold}",
        ]
        criteria = behavior.description

    return GEval(
        name=behavior.behavior_id,
        criteria=criteria,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        evaluation_steps=evaluation_steps,
        threshold=behavior.threshold / 10.0,
        model=model,
    )


def create_test_cases(
    behavior: BehaviorSpec,
    bundles: list[RunArtifactBundle],
    qualitative_rubric: Optional[QualitativeRubric] = None,
) -> list[LLMTestCase]:
    """
    Create test cases for all rollout bundles.

    Args:
        behavior: The behavior to test
        bundles: List of execution bundles from rollouts
        qualitative_rubric: Optional qualitative rubric for enhanced evaluation

    Returns:
        List of LLMTestCase objects for DeepEval
    """
    return [
        behavior_to_test_case(behavior, bundle, qualitative_rubric)
        for bundle in bundles
    ]
