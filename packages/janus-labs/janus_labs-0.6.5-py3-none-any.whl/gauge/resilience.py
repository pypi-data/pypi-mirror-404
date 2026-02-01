"""Rate limiting resilience for backend judge.

Implements circuit breaker and exponential backoff patterns for
handling HTTP 429 rate limit errors from the backend judge API.

JL-210.2: Rate Limit Resilience
"""

import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx


@dataclass
class CircuitState:
    """Internal state for circuit breaker."""
    failures: int = 0
    last_failure: Optional[datetime] = None
    is_open: bool = False


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.

    Opens after `failure_threshold` consecutive failures.
    Resets after `reset_timeout` seconds of no calls.
    """

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.threshold = failure_threshold
        self.reset_timeout = timedelta(seconds=reset_timeout)
        self._state = CircuitState()

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self._state.failures += 1
        self._state.last_failure = datetime.now()
        if self._state.failures >= self.threshold:
            self._state.is_open = True

    def record_success(self) -> None:
        """Record success and reset the circuit."""
        self._state = CircuitState()

    def reset(self) -> None:
        """Manually reset the circuit."""
        self._state = CircuitState()

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (should not make calls)."""
        if not self._state.is_open:
            return False
        # Check if reset timeout has elapsed
        if self._state.last_failure:
            elapsed = datetime.now() - self._state.last_failure
            if elapsed > self.reset_timeout:
                self._state = CircuitState()
                return False
        return True

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._state.failures


class ExponentialBackoff:
    """
    Exponential backoff iterator with jitter.

    Usage:
        for attempt, delay in ExponentialBackoff():
            try:
                result = make_request()
                break
            except RateLimitError:
                time.sleep(delay)
    """

    def __init__(
        self,
        base: float = 1.0,
        max_delay: float = 30.0,
        max_retries: int = 5,
        jitter: bool = True
    ):
        self.base = base
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.jitter = jitter

    def __iter__(self):
        for attempt in range(self.max_retries):
            delay = min(self.base * (2 ** attempt), self.max_delay)
            if self.jitter:
                delay += random.uniform(0, delay * 0.1)
            yield attempt, delay


class RateLimitError(Exception):
    """Raised when rate limit (HTTP 429) is encountered."""
    pass


@dataclass
class JudgeCallResult:
    """Result of a judge API call."""
    success: bool
    score: Optional[float] = None
    error: Optional[str] = None
    status: str = "OK"  # OK, RATE_LIMITED, CIRCUIT_OPEN, ERROR


class ResilientJudgeClient:
    """
    HTTP client with circuit breaker and exponential backoff.

    Handles rate limiting gracefully and prompts user for fallback
    when circuit opens.
    """

    def __init__(
        self,
        base_url: str,
        interactive: bool = True,
        timeout: float = 30.0,
        request_spacing: float = 1.2,
    ):
        self.base_url = base_url
        self.interactive = interactive
        self.timeout = timeout
        self.request_spacing = request_spacing
        self.circuit = CircuitBreaker(failure_threshold=5, reset_timeout=60)
        self.backoff = ExponentialBackoff(base=1.0, max_delay=30.0, max_retries=3)
        self._fallback_mode: Optional[str] = None
        self._last_request_time: Optional[float] = None

    def judge(self, payload: dict) -> JudgeCallResult:
        """
        Make judge API call with resilience.

        Returns JudgeCallResult with status indicating outcome.
        """
        # Enforce request spacing to avoid rate limits
        if self._last_request_time is not None and self.request_spacing > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.request_spacing:
                wait_time = self.request_spacing - elapsed
                time.sleep(wait_time)

        # Check circuit state
        if self.circuit.is_open:
            if self._fallback_mode is None:
                self._fallback_mode = self._prompt_fallback()

            if self._fallback_mode == "abort":
                return JudgeCallResult(
                    success=False,
                    status="CIRCUIT_OPEN",
                    error="Circuit breaker open - user aborted"
                )
            elif self._fallback_mode == "mock":
                return JudgeCallResult(
                    success=False,
                    status="CIRCUIT_OPEN",
                    error="Circuit breaker open - using mock scoring"
                )
            # wait mode: circuit will check timeout on next call

        # Try with backoff
        last_error = None
        for attempt, delay in self.backoff:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/judge",
                        json=payload
                    )

                    if response.status_code == 200:
                        self.circuit.record_success()
                        self._last_request_time = time.time()
                        result = response.json()
                        return JudgeCallResult(
                            success=True,
                            score=result.get("score", 0.0) / 100.0,
                            status="OK"
                        )
                    elif response.status_code == 429:
                        self.circuit.record_failure()
                        last_error = f"Rate limited (429) on attempt {attempt + 1}"
                        print(f"Backend judge: 429 rate limited, retry in {delay:.1f}s",
                              file=sys.stderr)

                        if self.circuit.is_open:
                            break  # Exit retry loop, handle circuit open

                        time.sleep(delay)
                    else:
                        self.circuit.record_failure()
                        last_error = f"HTTP {response.status_code}"
                        time.sleep(delay)

            except httpx.TimeoutException:
                self.circuit.record_failure()
                last_error = "Request timeout"
                time.sleep(delay)
            except Exception as e:
                self.circuit.record_failure()
                last_error = str(e)
                time.sleep(delay)

        # Exhausted retries or circuit opened
        if self.circuit.is_open and self._fallback_mode is None:
            self._fallback_mode = self._prompt_fallback()

        return JudgeCallResult(
            success=False,
            status="RATE_LIMITED" if "429" in (last_error or "") else "ERROR",
            error=last_error
        )

    def _prompt_fallback(self) -> str:
        """Prompt user for fallback action when circuit opens."""
        if not self.interactive:
            print("Backend rate limited. Using mock scoring (--no-interactive).",
                  file=sys.stderr)
            return "mock"

        print()
        print("=" * 60)
        print("  BACKEND RATE LIMITED")
        print("=" * 60)
        print()
        print(f"  The backend judge has failed {self.circuit.failure_count} times.")
        print("  How would you like to proceed?")
        print()
        print("  [1] Wait 60s and retry")
        print("  [2] Switch to mock scoring (offline, deterministic)")
        print("  [3] Abort run")
        print()

        try:
            choice = input("  Select [1-3]: ").strip()
            if choice == "1":
                print("  Waiting 60s for rate limit reset...")
                time.sleep(60)
                self.circuit.reset()
                return "wait"
            elif choice == "2":
                return "mock"
            else:
                return "abort"
        except (EOFError, KeyboardInterrupt):
            print("\n  Aborted.")
            return "abort"

    @property
    def should_use_mock(self) -> bool:
        """Check if we should fall back to mock scoring."""
        return self._fallback_mode == "mock"
