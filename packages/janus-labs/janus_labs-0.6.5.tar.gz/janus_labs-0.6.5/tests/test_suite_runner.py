"""Tests for suite runner."""

from forge.behavior import BehaviorSpec
from suite.definition import BenchmarkSuite
from suite.runner import SuiteRunConfig, run_suite


def test_suite_runner_executes_all_behaviors():
    behavior_a = BehaviorSpec(
        behavior_id="BHV-A",
        name="Behavior A",
        description="A",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )
    behavior_b = BehaviorSpec(
        behavior_id="BHV-B",
        name="Behavior B",
        description="B",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    suite = BenchmarkSuite(
        suite_id="suite-test",
        version="1.0.0",
        display_name="Suite Test",
        description="Suite test",
        behaviors=[behavior_a, behavior_b],
        rollouts_per_behavior=2,
    )

    calls = []

    def execute_fn(rollout_index: int, behavior_id: str):
        calls.append((behavior_id, rollout_index))
        return {"score": 0.8}

    config = SuiteRunConfig(suite=suite)
    result = run_suite(config, execute_fn)

    assert len(calls) == 4
    assert calls[:2] == [("BHV-A", 0), ("BHV-A", 1)]
    assert calls[2:] == [("BHV-B", 0), ("BHV-B", 1)]
    assert result.comparability_key == "suite-test:1.0.0"
