"""
Gate SDK - Metrics Collector

Collects counters and latency metrics for observability.
"""

from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Metrics:
    """Metrics snapshot"""

    requests_total: int = 0
    allowed_total: int = 0
    blocked_total: int = 0
    stepup_total: int = 0
    timeouts_total: int = 0
    errors_total: int = 0
    circuit_breaker_open_total: int = 0
    would_block_total: int = 0  # Shadow mode would-block count
    fail_open_total: int = 0  # Fail-open count
    latency_ms: List[int] = field(default_factory=list)


MetricsHook = Callable[[Metrics], None]


class MetricsCollector:
    """Metrics Collector"""

    def __init__(self):
        """Initialize metrics collector"""
        self._requests_total = 0
        self._allowed_total = 0
        self._blocked_total = 0
        self._stepup_total = 0
        self._timeouts_total = 0
        self._errors_total = 0
        self._circuit_breaker_open_total = 0
        self._would_block_total = 0  # Shadow mode would-block count
        self._fail_open_total = 0  # Fail-open count
        self._latency_ms: List[int] = []

        self._max_samples = 1000  # Keep last 1000 samples
        self._hooks: List[MetricsHook] = []

    def record_request(self, decision: str, latency_ms: int) -> None:
        """
        Record a request.

        Args:
            decision: Decision type ('ALLOW', 'BLOCK', 'REQUIRE_STEP_UP', 'WOULD_BLOCK', 'FAIL_OPEN')
            latency_ms: Request latency in milliseconds
        """
        self._requests_total += 1

        if decision == "ALLOW":
            self._allowed_total += 1
        elif decision == "BLOCK":
            self._blocked_total += 1
        elif decision == "REQUIRE_STEP_UP":
            self._stepup_total += 1
        elif decision == "WOULD_BLOCK":
            self._would_block_total += 1
            self._allowed_total += 1  # Count as allowed (shadow mode)
        elif decision == "FAIL_OPEN":
            self._fail_open_total += 1
            self._allowed_total += 1  # Count as allowed (fail-open)

        # Add latency sample (keep rolling window)
        self._latency_ms.append(latency_ms)
        if len(self._latency_ms) > self._max_samples:
            self._latency_ms.pop(0)  # Remove oldest sample

        self._emit_metrics()

    def record_timeout(self) -> None:
        """Record a timeout"""
        self._timeouts_total += 1
        self._errors_total += 1
        self._emit_metrics()

    def record_error(self) -> None:
        """Record an error"""
        self._errors_total += 1
        self._emit_metrics()

    def record_circuit_breaker_open(self) -> None:
        """Record circuit breaker open"""
        self._circuit_breaker_open_total += 1
        self._emit_metrics()

    def get_metrics(self) -> Metrics:
        """Get current metrics snapshot"""
        return Metrics(
            requests_total=self._requests_total,
            allowed_total=self._allowed_total,
            blocked_total=self._blocked_total,
            stepup_total=self._stepup_total,
            timeouts_total=self._timeouts_total,
            errors_total=self._errors_total,
            circuit_breaker_open_total=self._circuit_breaker_open_total,
            would_block_total=self._would_block_total,
            fail_open_total=self._fail_open_total,
            latency_ms=list(self._latency_ms),  # Copy list
        )

    def register_hook(self, hook: MetricsHook) -> None:
        """
        Register a metrics hook (e.g., for Prometheus/OpenTelemetry export).

        Args:
            hook: Callable that receives Metrics object
        """
        self._hooks.append(hook)

    def _emit_metrics(self) -> None:
        """Emit metrics to all registered hooks"""
        metrics = self.get_metrics()
        for hook in self._hooks:
            try:
                hook(metrics)
            except Exception as error:
                # Don't throw - metrics hooks should not break SDK
                import sys
                print(f"Error in metrics hook: {error}", file=sys.stderr)

    def reset(self) -> None:
        """Reset all metrics"""
        self._requests_total = 0
        self._allowed_total = 0
        self._blocked_total = 0
        self._stepup_total = 0
        self._timeouts_total = 0
        self._errors_total = 0
        self._circuit_breaker_open_total = 0
        self._would_block_total = 0
        self._fail_open_total = 0
        self._latency_ms = []

