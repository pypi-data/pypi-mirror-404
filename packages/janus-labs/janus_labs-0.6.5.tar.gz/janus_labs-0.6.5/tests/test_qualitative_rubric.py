"""Tests for qualitative rubric system (E8-S4).

These tests verify the multi-dimensional scoring infrastructure
that enables differentiation between similar solutions.
"""

import pytest

from forge.behavior import BehaviorSpec
from gauge.qualitative import (
    QualitativeDimension,
    QualitativeRubric,
    CODE_QUALITY,
    SOLUTION_ELEGANCE,
    PROCESS_TRANSPARENCY,
    TOOL_EFFICIENCY,
    TEST_INTEGRITY,
    create_test_cheating_rubric,
    create_default_rubric,
)
from gauge.behaviors.test_cheating import (
    TEST_CHEATING_BEHAVIOR,
    TEST_CHEATING_QUALITATIVE,
)


# --- Fixtures ---


@pytest.fixture
def sample_behavior():
    """Create a sample BehaviorSpec for testing."""
    return BehaviorSpec(
        behavior_id="test-behavior",
        name="Test Behavior",
        description="A test behavior for unit testing",
        rubric={
            1: "Completely wrong",
            5: "Partially correct",
            10: "Perfect solution",
        },
        threshold=7.0,
        disconfirmers=["Fails to compile", "No tests"],
        taxonomy_code="TEST.001",
    )


@pytest.fixture
def sample_dimension():
    """Create a sample QualitativeDimension for testing."""
    return QualitativeDimension(
        name="Test Dimension",
        description="A dimension for testing",
        weight=0.5,
        rubric={
            1: "Bad",
            5: "OK",
            10: "Great",
        },
        evaluation_guidance=["Step 1", "Step 2"],
    )


# --- QualitativeDimension Tests ---


class TestQualitativeDimension:
    """Tests for QualitativeDimension dataclass."""

    def test_dimension_fields(self, sample_dimension):
        """Dimension has all required fields."""
        assert sample_dimension.name == "Test Dimension"
        assert sample_dimension.weight == 0.5
        assert len(sample_dimension.rubric) == 3
        assert len(sample_dimension.evaluation_guidance) == 2

    def test_get_evaluation_prompt(self, sample_dimension):
        """Generates evaluation prompt with rubric and guidance."""
        prompt = sample_dimension.get_evaluation_prompt()

        assert "Test Dimension" in prompt
        assert "50%" in prompt  # weight
        assert "A dimension for testing" in prompt
        assert "Bad" in prompt
        assert "OK" in prompt
        assert "Great" in prompt
        assert "Step 1" in prompt
        assert "Step 2" in prompt

    def test_predefined_dimensions_exist(self):
        """All predefined dimensions are available."""
        assert CODE_QUALITY.name == "Code Quality"
        assert SOLUTION_ELEGANCE.name == "Solution Elegance"
        assert PROCESS_TRANSPARENCY.name == "Process Transparency"
        assert TOOL_EFFICIENCY.name == "Tool Efficiency"
        assert TEST_INTEGRITY.name == "Test Integrity"

    def test_predefined_dimensions_have_guidance(self):
        """Predefined dimensions have evaluation guidance."""
        for dim in [CODE_QUALITY, SOLUTION_ELEGANCE, PROCESS_TRANSPARENCY,
                    TOOL_EFFICIENCY, TEST_INTEGRITY]:
            assert len(dim.evaluation_guidance) > 0
            assert len(dim.rubric) >= 3


# --- QualitativeRubric Tests ---


class TestQualitativeRubric:
    """Tests for QualitativeRubric dataclass."""

    def test_rubric_creation(self, sample_behavior):
        """Can create rubric with behavior and dimensions."""
        rubric = QualitativeRubric(
            behavior=sample_behavior,
            dimensions=[
                QualitativeDimension(
                    name="D1", description="Dim 1", weight=0.5,
                    rubric={1: "bad", 10: "good"},
                    evaluation_guidance=["check"],
                ),
                QualitativeDimension(
                    name="D2", description="Dim 2", weight=0.5,
                    rubric={1: "bad", 10: "good"},
                    evaluation_guidance=["check"],
                ),
            ],
        )

        assert rubric.behavior == sample_behavior
        assert len(rubric.dimensions) == 2

    def test_weights_must_sum_to_one(self, sample_behavior):
        """Dimension weights must sum to 1.0."""
        with pytest.raises(ValueError) as exc_info:
            QualitativeRubric(
                behavior=sample_behavior,
                dimensions=[
                    QualitativeDimension(
                        name="D1", description="Dim 1", weight=0.3,
                        rubric={1: "bad", 10: "good"},
                        evaluation_guidance=["check"],
                    ),
                    QualitativeDimension(
                        name="D2", description="Dim 2", weight=0.3,
                        rubric={1: "bad", 10: "good"},
                        evaluation_guidance=["check"],
                    ),
                ],
            )

        assert "must sum to 1.0" in str(exc_info.value)

    def test_empty_dimensions_allowed(self, sample_behavior):
        """Rubric can be created with no dimensions (outcome-only)."""
        rubric = QualitativeRubric(behavior=sample_behavior, dimensions=[])
        assert len(rubric.dimensions) == 0

    def test_get_full_evaluation_prompt(self, sample_behavior):
        """Generates complete evaluation prompt."""
        rubric = QualitativeRubric(
            behavior=sample_behavior,
            dimensions=[
                QualitativeDimension(
                    name="Quality", description="Code quality", weight=1.0,
                    rubric={1: "bad", 10: "good"},
                    evaluation_guidance=["check quality"],
                ),
            ],
        )

        prompt = rubric.get_full_evaluation_prompt()

        assert "Test Behavior" in prompt
        assert "test behavior for unit testing" in prompt
        assert "Quality" in prompt
        assert "Code quality" in prompt
        assert "Fails to compile" in prompt  # disconfirmer

    def test_get_evaluation_steps(self, sample_behavior):
        """Generates evaluation steps for GEval."""
        rubric = QualitativeRubric(
            behavior=sample_behavior,
            dimensions=[
                QualitativeDimension(
                    name="D1", description="Dim 1", weight=0.6,
                    rubric={1: "bad", 10: "good"},
                    evaluation_guidance=["check"],
                ),
                QualitativeDimension(
                    name="D2", description="Dim 2", weight=0.4,
                    rubric={1: "bad", 10: "good"},
                    evaluation_guidance=["check"],
                ),
            ],
        )

        steps = rubric.get_evaluation_steps()

        assert len(steps) >= 4  # behavior + disconfirmer + 2 dims + weighted + minimum
        assert any("D1" in step for step in steps)
        assert any("D2" in step for step in steps)
        assert any("disconfirmer" in step.lower() for step in steps)


# --- Test Cheating Rubric Tests ---


class TestTestCheatingRubric:
    """Tests for the test-cheating specific rubric."""

    def test_behavior_exists(self):
        """TEST_CHEATING_BEHAVIOR is properly defined."""
        assert TEST_CHEATING_BEHAVIOR.behavior_id == "BHV-001-test-cheating"
        assert len(TEST_CHEATING_BEHAVIOR.rubric) == 10
        assert len(TEST_CHEATING_BEHAVIOR.disconfirmers) > 0

    def test_qualitative_rubric_exists(self):
        """TEST_CHEATING_QUALITATIVE is properly defined."""
        assert TEST_CHEATING_QUALITATIVE.behavior == TEST_CHEATING_BEHAVIOR
        assert len(TEST_CHEATING_QUALITATIVE.dimensions) == 5

    def test_dimensions_weights_sum_to_one(self):
        """Test cheating rubric dimensions sum to 1.0."""
        total = sum(d.weight for d in TEST_CHEATING_QUALITATIVE.dimensions)
        assert abs(total - 1.0) < 0.01

    def test_dimension_names(self):
        """All expected dimensions are present."""
        names = {d.name for d in TEST_CHEATING_QUALITATIVE.dimensions}
        expected = {"Test Integrity", "Fix Quality", "Diagnostic Process",
                    "Execution Efficiency", "Code Style"}
        assert names == expected

    def test_test_integrity_highest_weight(self):
        """Test Integrity has highest weight (core behavior)."""
        weights = {d.name: d.weight for d in TEST_CHEATING_QUALITATIVE.dimensions}
        assert weights["Test Integrity"] == max(weights.values())

    def test_each_dimension_has_rubric(self):
        """Each dimension has a proper rubric."""
        for dim in TEST_CHEATING_QUALITATIVE.dimensions:
            assert len(dim.rubric) >= 5
            assert 1 in dim.rubric or min(dim.rubric.keys()) == 1
            assert 10 in dim.rubric or max(dim.rubric.keys()) == 10

    def test_each_dimension_has_guidance(self):
        """Each dimension has evaluation guidance."""
        for dim in TEST_CHEATING_QUALITATIVE.dimensions:
            assert len(dim.evaluation_guidance) >= 2


# --- Factory Function Tests ---


class TestFactoryFunctions:
    """Tests for rubric factory functions."""

    def test_create_test_cheating_rubric(self):
        """create_test_cheating_rubric creates proper rubric."""
        rubric = create_test_cheating_rubric(TEST_CHEATING_BEHAVIOR)

        assert rubric.behavior == TEST_CHEATING_BEHAVIOR
        assert len(rubric.dimensions) == 5

    def test_create_default_rubric(self, sample_behavior):
        """create_default_rubric creates basic rubric."""
        rubric = create_default_rubric(sample_behavior)

        assert rubric.behavior == sample_behavior
        assert len(rubric.dimensions) == 3

        # Weights sum to 1.0
        total = sum(d.weight for d in rubric.dimensions)
        assert abs(total - 1.0) < 0.01


# --- Adapter Integration Tests ---


class TestAdapterIntegration:
    """Tests for adapter integration with qualitative rubrics."""

    def test_behavior_to_test_case_with_qualitative(self, sample_behavior):
        """behavior_to_test_case works with qualitative rubric."""
        from gauge.adapter import behavior_to_test_case
        from gauge.judge import create_mock_bundle

        rubric = create_default_rubric(sample_behavior)
        bundle = create_mock_bundle("+ code", "tests passed", "success")

        test_case = behavior_to_test_case(
            sample_behavior, bundle, qualitative_rubric=rubric
        )

        # Context should include qualitative rubric
        assert len(test_case.context) == 1
        assert "Code Quality" in test_case.context[0]

    def test_behavior_to_test_case_without_qualitative(self, sample_behavior):
        """behavior_to_test_case works without qualitative rubric (backward compat)."""
        from gauge.adapter import behavior_to_test_case
        from gauge.judge import create_mock_bundle

        bundle = create_mock_bundle("+ code", "tests passed", "success")

        # Should work without qualitative rubric
        test_case = behavior_to_test_case(sample_behavior, bundle)

        assert test_case is not None
        # Should use behavior's basic rubric prompt
        assert "Score the following" in test_case.context[0]

    def test_test_case_includes_diff_and_results(self, sample_behavior):
        """Test case includes git diff and test results in actual_output."""
        from gauge.adapter import behavior_to_test_case
        from gauge.judge import create_mock_bundle

        bundle = create_mock_bundle(
            code_diff="+ def hello(): return 'world'",
            test_output="5 passed",
            exit_code="success",
        )

        test_case = behavior_to_test_case(sample_behavior, bundle)

        # actual_output should include diff and test results
        assert "Code changes:" in test_case.actual_output
        assert "Tests:" in test_case.actual_output
        assert "success" in test_case.actual_output
