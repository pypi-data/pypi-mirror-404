"""LLM-as-judge scoring using DeepEval GEval.

E8-S3: Implements qualitative scoring to achieve differentiation
that outcome-based scoring cannot provide.
"""

import os
from dataclasses import dataclass
from typing import Optional

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase

from forge.behavior import BehaviorSpec
from gauge.adapter import behavior_to_test_case, create_geval_metric
from harness.types import RunArtifactBundle


@dataclass
class JudgeResult:
    """Result of LLM judge evaluation."""

    geval_score: float  # 0.0-1.0 from GEval
    geval_score_10: float  # 0-10 scale for display
    reason: str  # GEval explanation
    outcome_score: float  # 0.0-1.0 from outcome scoring
    combined_score: float  # Weighted combination
    combined_score_10: float  # 0-10 scale for display
    model: str  # Judge model used


def score_with_judge(
    behavior: BehaviorSpec,
    bundle: RunArtifactBundle,
    outcome_score: float,
    model: str = "gpt-4o",
    outcome_weight: float = 0.4,
) -> JudgeResult:
    """
    Score using LLM-as-judge via GEval.

    Combines outcome-based scoring with qualitative LLM evaluation
    to produce differentiated scores that capture code quality,
    maintainability, and idiomatic patterns.

    Args:
        behavior: The behavior specification with rubric
        bundle: Captured agent execution artifacts
        outcome_score: Score from outcome-based scoring (0.0-1.0)
        model: LLM model for judging (default: gpt-4o)
        outcome_weight: Weight for outcome score (default: 0.4)

    Returns:
        JudgeResult with GEval and combined scores

    Raises:
        ValueError: If OPENAI_API_KEY not set (for OpenAI models)
    """
    # Validate API key for OpenAI models
    if model.startswith("gpt") and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable required for --judge flag. "
            "Set it or use --model claude-3-5-sonnet with ANTHROPIC_API_KEY."
        )

    if model.startswith("claude") and not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable required for Claude judge. "
            "Set it or use --model gpt-4o with OPENAI_API_KEY."
        )

    # Convert bundle to test case
    test_case = behavior_to_test_case(behavior, bundle)

    # Create GEval metric with model (must be set at construction in DeepEval 3.7+)
    metric = create_geval_metric(behavior, model=model)

    # Run evaluation
    metric.measure(test_case)

    # Calculate combined score
    geval_weight = 1.0 - outcome_weight
    combined = (outcome_weight * outcome_score) + (geval_weight * metric.score)

    return JudgeResult(
        geval_score=metric.score,
        geval_score_10=metric.score * 10,
        reason=metric.reason or "No explanation provided",
        outcome_score=outcome_score,
        combined_score=combined,
        combined_score_10=combined * 10,
        model=model,
    )


def create_mock_bundle(
    code_diff: str,
    test_output: str = "All tests passed",
    exit_code: str = "success",
) -> RunArtifactBundle:
    """
    Create a mock bundle for testing without full agent execution.

    Useful for E8 development and manual evaluation of code samples.

    Args:
        code_diff: The code changes to evaluate
        test_output: Test execution output
        exit_code: success/halt/error

    Returns:
        RunArtifactBundle suitable for GEval scoring
    """
    return {
        "transcript": [
            {"role": "user", "content": "Complete the task"},
            {"role": "assistant", "content": "I'll implement the solution."},
        ],
        "tool_traces": [
            {
                "tool_name": "write_file",
                "arguments": {"path": "solution.py"},
                "result": "ok",
                "duration_ms": 100,
                "timestamp": "2026-01-18T00:00:00Z",
            }
        ],
        "repo_diff": {
            "files_changed": ["solution.py"],
            "insertions": len(code_diff.split("\n")),
            "deletions": 0,
            "patch": code_diff,
        },
        "test_results": {
            "framework": "pytest",
            "passed": 12,
            "failed": 0,
            "skipped": 0,
            "output": test_output,
        },
        "timings": {
            "total_ms": 5000,
            "tool_time_ms": 1000,
            "model_time_ms": 4000,
        },
        "exit_code": exit_code,
    }


def load_bundle_from_file(bundle_path: str) -> RunArtifactBundle:
    """
    Load a bundle from a JSON file.

    Supports manual bundle creation for testing GEval
    before full bundle capture is implemented.

    Args:
        bundle_path: Path to bundle.json file

    Returns:
        Parsed RunArtifactBundle
    """
    import json
    from pathlib import Path

    path = Path(bundle_path)
    if not path.exists():
        raise FileNotFoundError(f"Bundle file not found: {bundle_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    required = ["transcript", "tool_traces", "repo_diff", "test_results", "timings", "exit_code"]
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"Bundle missing required fields: {missing}")

    return data
