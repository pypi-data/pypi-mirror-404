"""Integration tests for E3 Governance Gating."""

from forge.behavior import BehaviorSpec
from gauge.governed_rollout import GovernedRolloutConfig, execute_governed_rollouts
from gauge.report import GovernanceFlags, extract_governance_flags, generate_benchmark_report
from governance.bridge import GovernanceContext, GovernanceDecision, GovernanceResult, check_governance
from governance.memory import get_governance_history, persist_governance_decision


def test_governance_bridge_pass():
    """Test governance check returns PASS for first iteration."""
    context = GovernanceContext(
        rollout_index=0,
        behavior_id="test-behavior",
        target_dir=".",
    )

    result = check_governance(context)

    assert result.decision == GovernanceDecision.PASS
    assert result.should_halt is False


def test_governance_bridge_warn():
    """Test governance check returns WARN at iteration 2."""
    context = GovernanceContext(
        rollout_index=1,
        behavior_id="test-behavior",
        approach_history=["approach 1", "approach 1"],
        current_approach="approach 2",
        target_dir=".",
    )

    result = check_governance(context)

    assert result.decision in (GovernanceDecision.PASS, GovernanceDecision.WARN)


def test_governed_rollout_halts():
    """Test governed rollout stops on HALT."""
    call_count = 0

    def mock_execute(index: int):
        nonlocal call_count
        call_count += 1
        return {"iteration": index}

    def mock_approach(_output):
        return "repeat the exact same approach"

    config = GovernedRolloutConfig(
        behavior_id="halt-test",
        max_rollouts=10,
        halt_on_governance=True,
    )

    results = execute_governed_rollouts(
        config,
        mock_execute,
        extract_approach_fn=mock_approach,
    )

    assert len(results) <= config.max_rollouts
    if any(result.halted for result in results):
        assert results[-1].halted is True


def test_governance_memory_persistence(tmp_path):
    """Test governance decisions persist to memory tier."""
    (tmp_path / ".janus").mkdir()

    result = GovernanceResult(
        decision=GovernanceDecision.HALT,
        trigger="semantic",
        signals={"semantic": 0.92},
        recommendation="Try different approach",
        escalation_id="esc-abc123",
        should_halt=True,
    )

    success = persist_governance_decision(
        result,
        behavior_id="test-behavior",
        rollout_index=2,
        target_dir=str(tmp_path),
    )

    assert success is True

    history = get_governance_history(target_dir=str(tmp_path))
    assert len(history) == 1
    assert history[0]["decision"] == "halt"
    assert history[0]["trigger"] == "semantic"


def test_benchmark_report_governance_flags():
    """Test BenchmarkReport includes governance flags."""
    flags = GovernanceFlags(
        total_rollouts=10,
        completed_rollouts=7,
        halted_rollouts=3,
        halt_rate=0.3,
        triggers={"semantic": 2, "confidence": 1},
        escalation_ids=["esc-1", "esc-2", "esc-3"],
    )

    behavior = BehaviorSpec(
        behavior_id="test-behavior",
        name="Test Behavior",
        description="Test behavior",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    report = generate_benchmark_report(
        behaviors=[behavior],
        behavior_scores={"test-behavior": [0.85, 0.7, 0.9]},
        trust_elasticity_scores={"test-behavior": [75.0, 80.0, 78.0]},
        config_fingerprint="test-fingerprint",
        governance_flags=flags,
    )

    assert "governance" in report
    assert report["governance"]["total_rollouts"] == 10
    assert report["governance"]["halted_rollouts"] == 3
    assert report["governance"]["halt_rate"] == 0.3
    assert len(report["governance"]["escalation_ids"]) == 3


def test_e3_full_pipeline():
    """Test full E3 pipeline: governed rollouts -> report with flags."""
    execution_count = 0

    def mock_execute(index: int):
        nonlocal execution_count
        execution_count += 1
        return {"score": 8.0 - (index * 0.5)}

    config = GovernedRolloutConfig(
        behavior_id="e3-pipeline-test",
        max_rollouts=5,
        halt_on_governance=True,
    )

    results = execute_governed_rollouts(config, mock_execute)
    flags = extract_governance_flags(results)

    behavior = BehaviorSpec(
        behavior_id=config.behavior_id,
        name="E3 Pipeline Test",
        description="Pipeline test behavior",
        rubric={1: "bad", 10: "good"},
        threshold=7.0,
        disconfirmers=[],
        taxonomy_code="O-1.11",
    )

    scores = [r.execution_output.get("score", 0) for r in results if r.execution_output]
    report = generate_benchmark_report(
        behaviors=[behavior],
        behavior_scores={config.behavior_id: scores},
        trust_elasticity_scores={config.behavior_id: [70.0] * len(scores)},
        config_fingerprint="e3-test",
        governance_flags=flags,
    )

    assert report["behaviors"][0]["behavior_id"] == config.behavior_id
    assert "governance" in report
    assert report["governance"]["total_rollouts"] == len(results)
