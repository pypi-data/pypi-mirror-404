"""
Unit Tests for MetricsCollector
"""

import pytest
from gate_sdk.metrics import MetricsCollector, Metrics


class TestMetricsCollector:
    def test_record_request_allow(self):
        """Test recording ALLOW decision"""
        collector = MetricsCollector()
        collector.record_request("ALLOW", 50)

        metrics = collector.get_metrics()
        assert metrics.requests_total == 1
        assert metrics.allowed_total == 1
        assert metrics.blocked_total == 0
        assert metrics.stepup_total == 0
        assert 50 in metrics.latency_ms

    def test_record_request_block(self):
        """Test recording BLOCK decision"""
        collector = MetricsCollector()
        collector.record_request("BLOCK", 100)

        metrics = collector.get_metrics()
        assert metrics.requests_total == 1
        assert metrics.allowed_total == 0
        assert metrics.blocked_total == 1
        assert metrics.stepup_total == 0

    def test_record_request_stepup(self):
        """Test recording REQUIRE_STEP_UP decision"""
        collector = MetricsCollector()
        collector.record_request("REQUIRE_STEP_UP", 75)

        metrics = collector.get_metrics()
        assert metrics.requests_total == 1
        assert metrics.allowed_total == 0
        assert metrics.blocked_total == 0
        assert metrics.stepup_total == 1

    def test_record_timeout(self):
        """Test recording timeout"""
        collector = MetricsCollector()
        collector.record_timeout()

        metrics = collector.get_metrics()
        assert metrics.timeouts_total == 1
        assert metrics.errors_total == 1

    def test_record_error(self):
        """Test recording error"""
        collector = MetricsCollector()
        collector.record_error()

        metrics = collector.get_metrics()
        assert metrics.errors_total == 1

    def test_record_circuit_breaker_open(self):
        """Test recording circuit breaker open"""
        collector = MetricsCollector()
        collector.record_circuit_breaker_open()

        metrics = collector.get_metrics()
        assert metrics.circuit_breaker_open_total == 1

    def test_register_hook(self):
        """Test metrics hook registration"""
        collector = MetricsCollector()
        hook_called = []

        def hook(metrics: Metrics):
            hook_called.append(metrics)

        collector.register_hook(hook)
        collector.record_request("ALLOW", 50)

        assert len(hook_called) == 1
        assert hook_called[0].requests_total == 1

    def test_get_metrics_returns_copy(self):
        """Test get_metrics returns a copy"""
        collector = MetricsCollector()
        collector.record_request("ALLOW", 50)

        metrics1 = collector.get_metrics()
        metrics2 = collector.get_metrics()

        assert metrics1 is not metrics2  # Different objects
        assert metrics1.latency_ms is not metrics2.latency_ms  # Different lists
        assert metrics1 == metrics2  # Same values

    def test_reset(self):
        """Test metrics reset"""
        collector = MetricsCollector()
        collector.record_request("ALLOW", 50)
        collector.record_timeout()
        collector.record_error()
        collector.record_circuit_breaker_open()

        collector.reset()

        metrics = collector.get_metrics()
        assert metrics.requests_total == 0
        assert metrics.allowed_total == 0
        assert metrics.blocked_total == 0
        assert metrics.stepup_total == 0
        assert metrics.timeouts_total == 0
        assert metrics.errors_total == 0
        assert metrics.circuit_breaker_open_total == 0
        assert len(metrics.latency_ms) == 0

