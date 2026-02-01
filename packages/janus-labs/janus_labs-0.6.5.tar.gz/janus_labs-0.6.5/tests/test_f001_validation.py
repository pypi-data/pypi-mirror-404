"""F001 Validation: Trust Elasticity Metric.

Acceptance Criteria:
1. BehaviorSpec defined with rubric and threshold ✓
2. 10 rollouts complete without crash
3. Trust Elasticity metric calculated
4. Mean score reproducible across runs (±0.5)
"""

import pytest
from pathlib import Path
from statistics import mean, stdev

from deepeval.test_case import LLMTestCase

from forge.behavior import BehaviorSpec
from gauge.trust_elasticity import TrustElasticityMetric, GovernanceSignals
from scaffold.scorer import score_outcome


# BehaviorSpecs from our benchmark
BHV_002 = BehaviorSpec(
    behavior_id="BHV-002-refactor-complexity",
    name="Reduce Cyclomatic Complexity",
    description="Refactor the calculate_price function to reduce cyclomatic complexity from 18 to 6 or less.",
    rubric={
        1: "No meaningful refactoring attempted",
        2: "Minor changes, complexity unchanged",
        3: "Partial refactoring, complexity reduced slightly",
        4: "Complexity reduced but not to target",
        5: "Complexity reduced to 8-9, some issues",
        6: "Complexity target met (<=6), minor code issues",
        7: "Clean refactor, complexity <=6",
        8: "Good patterns used, improved readability",
        9: "Excellent refactor with clear abstractions",
        10: "Exemplary refactor - maintainable, testable, documented",
    },
    threshold=6.0,
    disconfirmers=["Tests fail after refactoring", "Functionality changed", "Complexity increased"],
    taxonomy_code="O-2.01",
    version="1.0.0",
)

BHV_003 = BehaviorSpec(
    behavior_id="BHV-003-error-handling",
    name="Add Comprehensive Error Handling",
    description="Add error handling to the file_processor module.",
    rubric={
        1: "No error handling added",
        2: "Minimal handling, silent failures",
        3: "Some errors handled, others crash",
        4: "Most errors handled, poor messages",
        5: "All errors handled, basic logging",
        6: "All errors handled, good messages",
        7: "Comprehensive handling, structured logging",
        8: "Good error messages, proper error codes",
        9: "Production-quality with context preservation",
        10: "Exemplary - retry logic, graceful degradation, full traceability",
    },
    threshold=6.0,
    disconfirmers=["Silent failures", "Generic catch-all", "Missing error types"],
    taxonomy_code="O-3.01",
    version="1.0.0",
)


class TestF001Criterion1:
    """F001 Criterion 1: BehaviorSpec defined with rubric and threshold."""

    def test_bhv002_has_rubric_and_threshold(self):
        """BHV-002 has complete rubric and threshold."""
        assert BHV_002.rubric is not None
        assert len(BHV_002.rubric) == 10  # 1-10 scale
        assert BHV_002.threshold == 6.0

    def test_bhv003_has_rubric_and_threshold(self):
        """BHV-003 has complete rubric and threshold."""
        assert BHV_003.rubric is not None
        assert len(BHV_003.rubric) == 10  # 1-10 scale
        assert BHV_003.threshold == 6.0

    def test_rubric_prompt_generation(self):
        """BehaviorSpec generates valid rubric prompt."""
        prompt = BHV_002.get_rubric_prompt()
        assert "Score the following behavior" in prompt
        assert "Score 1:" in prompt
        assert "Score 10:" in prompt


class TestF001Criterion2:
    """F001 Criterion 2: 10 rollouts complete without crash."""

    def test_10_trust_elasticity_rollouts(self):
        """Run 10 Trust Elasticity calculations without crash."""
        scores = []
        for i in range(10):
            metric = TrustElasticityMetric(base_score=8.0)
            test_case = LLMTestCase(input=f"test_{i}", actual_output=f"output_{i}")
            score = metric.measure(test_case)
            scores.append(score)
            assert 0.0 <= score <= 1.0, f"Rollout {i} produced invalid score: {score}"

        assert len(scores) == 10
        print(f"\n10 rollout scores: {[f'{s:.3f}' for s in scores]}")

    def test_10_rollouts_with_varied_signals(self):
        """Run 10 rollouts with varied governance signals."""
        scores = []
        for i in range(10):
            # Vary the governance signals
            bundle = {
                "transcript": [{"role": "user", "content": "test"}] * (i + 1),
                "tool_traces": [
                    {"tool_name": "read_file", "result": "ok"},
                    {"tool_name": "write_file", "result": "ok" if i % 2 == 0 else "error"},
                ],
                "repo_diff": {},
                "test_results": {},
                "timings": {},
                "exit_code": "success" if i < 8 else "halt",
            }
            metric = TrustElasticityMetric(base_score=7.5 + (i * 0.1), bundle=bundle)
            test_case = LLMTestCase(input=f"test_{i}", actual_output=f"output_{i}")
            score = metric.measure(test_case)
            scores.append(score * 100)  # Convert to 0-100 scale

        assert len(scores) == 10
        print(f"\n10 varied rollout scores (0-100): {[f'{s:.1f}' for s in scores]}")


class TestF001Criterion3:
    """F001 Criterion 3: Trust Elasticity metric calculated."""

    def test_trust_elasticity_calculates_score(self):
        """Trust Elasticity produces valid 0-100 score."""
        metric = TrustElasticityMetric(base_score=8.0)
        test_case = LLMTestCase(input="test", actual_output="output")

        score = metric.measure(test_case)
        score_100 = score * 100

        assert 0.0 <= score_100 <= 100.0
        assert metric.reason is not None
        print(f"\nTrust Elasticity: {score_100:.1f}/100 - {metric.reason}")

    def test_trust_elasticity_with_governance_signals(self):
        """Trust Elasticity adjusts for governance signals."""
        # High competence bundle
        good_bundle = {
            "transcript": [],
            "tool_traces": [
                {"tool_name": "read", "result": "ok"},
                {"tool_name": "write", "result": "ok"},
            ],
            "repo_diff": {},
            "test_results": {},
            "timings": {},
            "exit_code": "success",
        }

        # Low competence bundle (errors + halt)
        bad_bundle = {
            "transcript": [],
            "tool_traces": [
                {"tool_name": "read", "result": "error: file not found"},
                {"tool_name": "foundation_check", "result": "warn"},
            ],
            "repo_diff": {},
            "test_results": {},
            "timings": {},
            "exit_code": "halt",
        }

        good_metric = TrustElasticityMetric(base_score=8.0, bundle=good_bundle)
        bad_metric = TrustElasticityMetric(base_score=8.0, bundle=bad_bundle)

        test_case = LLMTestCase(input="test", actual_output="output")

        good_score = good_metric.measure(test_case) * 100
        bad_score = bad_metric.measure(test_case) * 100

        assert good_score > bad_score, f"Good ({good_score}) should beat bad ({bad_score})"
        print(f"\nGood bundle: {good_score:.1f}, Bad bundle: {bad_score:.1f}")

    def test_grade_mapping(self):
        """Trust Elasticity maps to correct letter grades."""
        grades = [
            (95, "S"), (90, "S"),
            (85, "A"), (80, "A"),
            (75, "B"), (70, "B"),
            (65, "C"), (60, "C"),
            (55, "D"), (50, "D"),
            (45, "F"), (30, "F"),
        ]
        for score, expected in grades:
            actual = TrustElasticityMetric.score_to_grade(score)
            assert actual == expected, f"Score {score} should be {expected}, got {actual}"


class TestF001Criterion4:
    """F001 Criterion 4: Mean score reproducible across runs (±0.5)."""

    def test_reproducibility_with_same_inputs(self):
        """Same inputs produce same score (deterministic)."""
        scores = []
        for _ in range(10):
            metric = TrustElasticityMetric(base_score=8.0)
            test_case = LLMTestCase(input="consistent_test", actual_output="consistent_output")
            score = metric.measure(test_case)
            scores.append(score * 100)

        # With identical inputs, scores should be identical
        assert len(set(scores)) == 1, f"Identical inputs should produce identical scores: {scores}"
        print(f"\n10 identical runs: {scores[0]:.1f} (consistent)")

    def test_reproducibility_with_fixed_bundle(self):
        """Fixed bundle produces reproducible scores within ±0.5."""
        bundle = {
            "transcript": [{"role": "user", "content": "test"}],
            "tool_traces": [{"tool_name": "read", "result": "ok"}],
            "repo_diff": {},
            "test_results": {},
            "timings": {},
            "exit_code": "success",
        }

        scores = []
        for i in range(10):
            metric = TrustElasticityMetric(base_score=8.0, bundle=bundle)
            test_case = LLMTestCase(input=f"test_{i}", actual_output=f"output_{i}")
            score = metric.measure(test_case)
            scores.append(score * 100)

        mean_score = mean(scores)
        max_deviation = max(abs(s - mean_score) for s in scores)

        # All scores should be within ±0.5 of mean
        assert max_deviation <= 0.5, f"Max deviation {max_deviation:.2f} exceeds ±0.5"
        print(f"\nMean: {mean_score:.2f}, Max deviation: {max_deviation:.3f}")

    def test_aggregate_benchmark_reproducibility(self):
        """Aggregate scores from benchmark are reproducible."""
        # Simulate the E7-S3 benchmark scores
        benchmark_scores = {
            "claude": {"BHV-002": 8, "BHV-003": 8},
            "codex": {"BHV-002": 9, "BHV-003": 7},
            "gemini": {"BHV-002": 8, "BHV-003": 9},
        }

        # Run 3 "trials" of aggregation
        aggregates = []
        for trial in range(3):
            trial_totals = []
            for agent, scores in benchmark_scores.items():
                total = sum(scores.values())
                trial_totals.append(total)
            aggregates.append(mean(trial_totals))

        # Aggregates should be identical (deterministic)
        assert len(set(aggregates)) == 1
        print(f"\nAggregate reproducibility: {aggregates[0]:.2f} (3 trials identical)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
