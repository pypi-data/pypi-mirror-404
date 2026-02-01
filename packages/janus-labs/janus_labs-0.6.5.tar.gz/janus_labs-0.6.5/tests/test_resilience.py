"""Tests for rate limiting resilience (JL-210.2)."""

import pytest
from gauge.resilience import CircuitBreaker, ExponentialBackoff, JudgeCallResult


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_starts_closed(self):
        """Circuit should start in closed state."""
        cb = CircuitBreaker()
        assert not cb.is_open
        assert cb.failure_count == 0

    def test_opens_after_threshold(self):
        """Circuit should open after failure_threshold consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open
        cb.record_failure()
        assert cb.is_open

    def test_stays_closed_below_threshold(self):
        """Circuit should stay closed below threshold."""
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert not cb.is_open
        assert cb.failure_count == 4

    def test_resets_on_success(self):
        """Circuit should reset on success."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        cb.record_success()
        assert not cb.is_open
        assert cb.failure_count == 0

    def test_manual_reset(self):
        """Circuit can be manually reset."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        cb.reset()
        assert not cb.is_open
        assert cb.failure_count == 0

    def test_default_threshold(self):
        """Default threshold should be 5."""
        cb = CircuitBreaker()
        for _ in range(4):
            cb.record_failure()
        assert not cb.is_open
        cb.record_failure()
        assert cb.is_open


class TestExponentialBackoff:
    """Tests for ExponentialBackoff class."""

    def test_increases_delay(self):
        """Delays should increase exponentially."""
        backoff = ExponentialBackoff(base=1.0, max_delay=30.0, max_retries=5, jitter=False)
        delays = [delay for _, delay in backoff]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_caps_at_max(self):
        """Delays should be capped at max_delay."""
        backoff = ExponentialBackoff(base=1.0, max_delay=5.0, max_retries=5, jitter=False)
        delays = [delay for _, delay in backoff]
        assert all(d <= 5.0 for d in delays)
        assert delays == [1.0, 2.0, 4.0, 5.0, 5.0]

    def test_custom_base(self):
        """Custom base delay should work."""
        backoff = ExponentialBackoff(base=2.0, max_delay=100.0, max_retries=3, jitter=False)
        delays = [delay for _, delay in backoff]
        assert delays == [2.0, 4.0, 8.0]

    def test_respects_max_retries(self):
        """Should only yield max_retries attempts."""
        backoff = ExponentialBackoff(max_retries=3, jitter=False)
        attempts = list(backoff)
        assert len(attempts) == 3

    def test_jitter_adds_variance(self):
        """With jitter enabled, delays should have variance."""
        backoff = ExponentialBackoff(base=1.0, max_delay=30.0, max_retries=5, jitter=True)
        delays = [delay for _, delay in backoff]
        # With jitter, delays should be slightly higher than base delays
        assert all(d >= 1.0 for d in delays)  # At least base delay
        # Check first delay has jitter (should be 1.0 + some jitter)
        assert delays[0] >= 1.0 and delays[0] <= 1.1


class TestJudgeCallResult:
    """Tests for JudgeCallResult dataclass."""

    def test_success_result(self):
        """Successful result should have score."""
        result = JudgeCallResult(success=True, score=0.85, status="OK")
        assert result.success
        assert result.score == 0.85
        assert result.status == "OK"
        assert result.error is None

    def test_failure_result(self):
        """Failed result should have error."""
        result = JudgeCallResult(
            success=False,
            status="RATE_LIMITED",
            error="Rate limited (429) on attempt 3"
        )
        assert not result.success
        assert result.score is None
        assert result.status == "RATE_LIMITED"
        assert "429" in result.error

    def test_default_status(self):
        """Default status should be OK."""
        result = JudgeCallResult(success=True, score=0.5)
        assert result.status == "OK"
