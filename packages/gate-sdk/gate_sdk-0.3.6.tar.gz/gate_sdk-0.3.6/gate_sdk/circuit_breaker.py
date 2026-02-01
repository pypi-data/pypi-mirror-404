"""
Gate SDK - Circuit Breaker

Prevents cascading failures by opening the circuit after consecutive failures.
"""

from typing import Literal, Optional
from dataclasses import dataclass


CircuitState = Literal["CLOSED", "OPEN", "HALF_OPEN"]


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    trip_after_consecutive_failures: int = 5
    cool_down_ms: int = 30000  # 30 seconds


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics"""

    failures: int
    successes: int
    state: CircuitState
    last_failure_time: Optional[int] = None
    last_success_time: Optional[int] = None
    trips_to_open: int = 0


class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open"""

    def __init__(self, message: str):
        super().__init__(message)
        self.name = "CircuitBreakerOpenError"


class CircuitBreaker:
    """Circuit Breaker implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self._state: CircuitState = "CLOSED"
        self._failures = 0
        self._successes = 0
        self._last_failure_time: Optional[int] = None
        self._last_success_time: Optional[int] = None
        self._trips_to_open = 0

        self._trip_threshold = config.trip_after_consecutive_failures
        self._cool_down_ms = config.cool_down_ms

    def execute(self, fn):
        """
        Execute function with circuit breaker protection.

        Args:
            fn: Async function to execute

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self._state == "OPEN":
            import time

            now_ms = int(time.time() * 1000)
            time_since_last_failure = (
                now_ms - self._last_failure_time if self._last_failure_time else float("inf")
            )

            if time_since_last_failure >= self._cool_down_ms:
                self._state = "HALF_OPEN"
                self._failures = 0  # Reset failures for half-open probe
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Will retry after {self._cool_down_ms - time_since_last_failure}ms"
                )

        try:
            result = fn()
            self._on_success()
            return result
        except Exception as error:
            self._on_failure()
            raise error

    def _on_success(self) -> None:
        """Handle successful execution"""
        import time

        self._successes += 1
        self._last_success_time = int(time.time() * 1000)

        if self._state == "HALF_OPEN":
            # Successful probe - close circuit
            self._state = "CLOSED"
            self._failures = 0
        elif self._state == "CLOSED":
            # Success in closed state - reset failure count
            self._failures = 0

    def _on_failure(self) -> None:
        """Handle failed execution"""
        import time

        self._failures += 1
        self._last_failure_time = int(time.time() * 1000)

        if self._state == "HALF_OPEN":
            # Failed probe - open circuit again
            self._state = "OPEN"
            self._trips_to_open += 1
        elif self._state == "CLOSED" and self._failures >= self._trip_threshold:
            # Too many failures - open circuit
            self._state = "OPEN"
            self._trips_to_open += 1

    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics"""
        return CircuitBreakerMetrics(
            failures=self._failures,
            successes=self._successes,
            state=self._state,
            last_failure_time=self._last_failure_time,
            last_success_time=self._last_success_time,
            trips_to_open=self._trips_to_open,
        )

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state"""
        self._state = "CLOSED"
        self._failures = 0
        self._successes = 0
        self._last_failure_time = None
        self._last_success_time = None
        self._trips_to_open = 0

