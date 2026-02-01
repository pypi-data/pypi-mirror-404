"""
Unit Tests for CircuitBreaker
"""

import pytest
import time
from gate_sdk.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitBreakerConfig


class TestCircuitBreaker:
    def test_execute_success_in_closed_state(self):
        """Test successful execution in CLOSED state"""
        config = CircuitBreakerConfig(
            trip_after_consecutive_failures=3,
            cool_down_ms=1000,
        )
        breaker = CircuitBreaker(config)

        def success_fn():
            return "success"

        result = breaker.execute(success_fn)
        assert result == "success"

        metrics = breaker.get_metrics()
        assert metrics.state == "CLOSED"
        assert metrics.successes == 1
        assert metrics.failures == 0

    def test_open_circuit_after_consecutive_failures(self):
        """Test circuit opens after consecutive failures"""
        config = CircuitBreakerConfig(
            trip_after_consecutive_failures=3,
            cool_down_ms=1000,
        )
        breaker = CircuitBreaker(config)

        def fail_fn():
            raise Exception("failure")

        # Fail 3 times (trip threshold)
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.execute(fail_fn)

        # Next call should throw CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.execute(fail_fn)

        metrics = breaker.get_metrics()
        assert metrics.state == "OPEN"
        assert metrics.trips_to_open == 1

    def test_half_open_after_cooldown(self):
        """Test circuit transitions to HALF_OPEN after cool-down"""
        config = CircuitBreakerConfig(
            trip_after_consecutive_failures=3,
            cool_down_ms=100,  # Short cooldown for testing
        )
        breaker = CircuitBreaker(config)

        def fail_fn():
            raise Exception("failure")

        # Open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.execute(fail_fn)

        # Wait for cool-down
        time.sleep(0.15)

        # Should transition to HALF_OPEN
        def success_fn():
            return "success"

        result = breaker.execute(success_fn)
        assert result == "success"

        metrics = breaker.get_metrics()
        assert metrics.state == "CLOSED"  # Successful probe closes circuit

    def test_get_metrics(self):
        """Test metrics retrieval"""
        config = CircuitBreakerConfig()
        breaker = CircuitBreaker(config)

        metrics = breaker.get_metrics()
        assert metrics.failures == 0
        assert metrics.successes == 0
        assert metrics.state == "CLOSED"
        assert metrics.trips_to_open == 0

    def test_reset(self):
        """Test circuit breaker reset"""
        config = CircuitBreakerConfig(
            trip_after_consecutive_failures=3,
            cool_down_ms=1000,
        )
        breaker = CircuitBreaker(config)

        def fail_fn():
            raise Exception("failure")

        # Open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.execute(fail_fn)

        breaker.reset()

        metrics = breaker.get_metrics()
        assert metrics.state == "CLOSED"
        assert metrics.failures == 0
        assert metrics.successes == 0
        assert metrics.trips_to_open == 0

