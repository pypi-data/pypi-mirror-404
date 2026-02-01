"""Tests for standalone operation without mcp-janus."""

import sys
from pathlib import Path

# Ensure we import from janus-labs, not mcp-janus
_janus_labs_root = Path(__file__).resolve().parents[1]
if str(_janus_labs_root) not in sys.path:
    sys.path.insert(0, str(_janus_labs_root))

# Import from local janus_types (remove any cached mcp-janus version)
if "janus_types" in sys.modules:
    del sys.modules["janus_types"]

from janus_types import (  # noqa: E402
    TrustScore,
    GovernanceState,
    foundation_check,
    handle_escalation,
    infer_confidence,
)


class TestJanusTypesStub:
    """Test stub implementations."""

    def test_trust_score_default(self):
        """Default trust score should have standard values."""
        score = TrustScore.default()
        assert score.value == 0.7
        assert score.confidence == 0.5

    def test_trust_score_custom(self):
        """Custom trust score should accept values."""
        score = TrustScore(value=0.9, confidence=0.8)
        assert score.value == 0.9
        assert score.confidence == 0.8

    def test_governance_state_defaults(self):
        """Governance state should have sensible defaults."""
        state = GovernanceState()
        assert state.iteration_count == 1
        assert state.halted is False
        assert state.trust_score is None

    def test_governance_state_with_trust(self):
        """Governance state should accept trust score."""
        trust = TrustScore.default()
        state = GovernanceState(iteration_count=2, trust_score=trust)
        assert state.iteration_count == 2
        assert state.trust_score.value == 0.7

    def test_foundation_check_pass_iteration_one(self):
        """First iteration should pass."""
        result = foundation_check(iteration_count=1)
        assert result["result"] == "PASS"
        assert result["trigger"] == "none"

    def test_foundation_check_pass_iteration_two(self):
        """Second iteration should pass."""
        result = foundation_check(iteration_count=2)
        assert result["result"] == "PASS"

    def test_foundation_check_warn_at_three(self):
        """Third iteration without pattern should warn."""
        result = foundation_check(iteration_count=3, same_pattern=False)
        assert result["result"] == "WARN"
        assert result["trigger"] == "iteration"

    def test_foundation_check_halt_with_pattern(self):
        """Third iteration with same pattern should halt."""
        result = foundation_check(iteration_count=3, same_pattern=True)
        assert result["result"] == "HALT"
        assert result["trigger"] == "iteration"

    def test_foundation_check_signals(self):
        """Foundation check should include iteration in signals."""
        result = foundation_check(iteration_count=5)
        assert result["signals"]["iteration"] == 5

    def test_infer_confidence_returns_moderate(self):
        """Confidence inference should return moderate values."""
        confidence, label = infer_confidence("any text here")
        assert confidence == 0.7
        assert label == "moderate"

    def test_infer_confidence_ignores_input(self):
        """Stub always returns same value regardless of input."""
        conf1, _ = infer_confidence("very confident!")
        conf2, _ = infer_confidence("uncertain...")
        assert conf1 == conf2

    def test_handle_escalation_logs(self):
        """Escalation handler should log but take no action."""
        result = handle_escalation({}, {})
        assert result["action"] == "logged"
        assert result["escalation_id"] is None

    def test_handle_escalation_with_context(self):
        """Escalation handler should accept context."""
        result = handle_escalation(
            {"result": "HALT"},
            {"target_dir": "/tmp/test"},
        )
        assert result["action"] == "logged"
