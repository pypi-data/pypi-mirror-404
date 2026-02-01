"""Tests for BHV-002 Instruction Adherence and BHV-003 Code Quality."""

from unittest.mock import MagicMock, patch

import pytest
from deepeval.test_case import LLMTestCaseParams

from gauge.behaviors.code_quality import CodeQualityBehavior
from gauge.behaviors.instruction_adherence import InstructionAdherenceBehavior


@patch("gauge.behaviors.instruction_adherence.InstructionFollowingMetric")
def test_instruction_adherence_follows_instructions(mock_metric_cls):
    """Agent that follows instructions should score high."""
    mock_metric = MagicMock()
    mock_metric.measure.return_value = 0.92
    mock_metric_cls.return_value = mock_metric

    behavior = InstructionAdherenceBehavior(threshold=0.7, model="gpt-4o")
    score = behavior.evaluate("Return 'ok'", "ok")

    assert score == pytest.approx(92.0)
    mock_metric.measure.assert_called_once()


@patch("gauge.behaviors.instruction_adherence.InstructionFollowingMetric")
def test_instruction_adherence_detects_scope_creep(mock_metric_cls):
    """Agent that adds unrequested features should score lower."""
    mock_metric = MagicMock()
    mock_metric.measure.return_value = 0.35
    mock_metric_cls.return_value = mock_metric

    behavior = InstructionAdherenceBehavior(threshold=0.7, model="gpt-4o")
    score = behavior.evaluate("Return 'ok'", "ok plus extras")

    assert score < 70.0


@patch("gauge.behaviors.code_quality.GEval")
def test_code_quality_correct_code(mock_geval_cls):
    """Correct, minimal, idiomatic code should score high."""
    mock_metric = MagicMock()
    mock_metric.measure.return_value = 0.88
    mock_geval_cls.return_value = mock_metric

    behavior = CodeQualityBehavior(model="gpt-4o")
    score = behavior.evaluate("Fix the bug", "def fix(): return True")

    assert score == pytest.approx(88.0)
    _, kwargs = mock_geval_cls.call_args
    assert kwargs["criteria"] == behavior.CRITERIA
    assert kwargs["evaluation_params"] == [
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
    ]


@patch("gauge.behaviors.code_quality.GEval")
def test_code_quality_detects_issues(mock_geval_cls):
    """Code with style issues or scope creep should score lower."""
    mock_metric = MagicMock()
    mock_metric.measure.return_value = 0.3
    mock_geval_cls.return_value = mock_metric

    behavior = CodeQualityBehavior(model="gpt-4o")
    score = behavior.evaluate("Fix the bug", "def fix(): return True  # plus extras")

    assert score < 50.0
