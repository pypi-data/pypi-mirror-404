"""
Gate SDK - Step-Up Polling

Polls Gate Hot Path step-up status endpoint until decision is reached.
"""

import time
from typing import Dict, Any, Optional

from .errors import GateError, GateNotFoundError, StepUpTimeoutError
from .types import StepUpStatusResponse, StepUpStatus, StepUpFinalResult
from .http import HttpClient
from .utils import clamp, now_epoch_seconds

DEFAULT_POLLING_INTERVAL_MS = 250
DEFAULT_MAX_WAIT_MS = 15000
DEFAULT_TTL_MIN_SECONDS = 300
DEFAULT_TTL_MAX_SECONDS = 900
DEFAULT_TTL_DEFAULT_SECONDS = 600


class StepUpPoller:
    """Step-up polling helper"""

    def __init__(
        self,
        http_client: HttpClient,
        tenant_id: str,
        polling_interval_ms: int = DEFAULT_POLLING_INTERVAL_MS,
        max_wait_ms: int = DEFAULT_MAX_WAIT_MS,
        ttl_min_seconds: int = DEFAULT_TTL_MIN_SECONDS,
        ttl_max_seconds: int = DEFAULT_TTL_MAX_SECONDS,
        ttl_default_seconds: int = DEFAULT_TTL_DEFAULT_SECONDS,
    ):
        """
        Initialize step-up poller.

        Args:
            http_client: HTTP client instance
            tenant_id: Tenant ID
            polling_interval_ms: Polling interval in milliseconds
            max_wait_ms: Maximum wait time in milliseconds
            ttl_min_seconds: Minimum TTL in seconds (guardrail)
            ttl_max_seconds: Maximum TTL in seconds (guardrail)
            ttl_default_seconds: Default TTL in seconds
        """
        self.http_client = http_client
        self.tenant_id = tenant_id
        self.polling_interval_ms = polling_interval_ms
        self.max_wait_ms = max_wait_ms
        self.ttl_min_seconds = ttl_min_seconds
        self.ttl_max_seconds = ttl_max_seconds
        self.ttl_default_seconds = ttl_default_seconds

    def get_status(self, request_id: str) -> StepUpStatusResponse:
        """
        Get current step-up status.

        Args:
            request_id: Step-up request ID

        Returns:
            Step-up status response

        Raises:
            GateNotFoundError: If request not found
            GateError: For other errors
        """
        from urllib.parse import urlencode

        params = urlencode({
            "tenantId": self.tenant_id,
            "requestId": request_id,
        })
        path = f"/defense/stepup/status?{params}"

        try:
            # API returns snake_case, convert to camelCase
            response = self.http_client.request(
                method="GET",
                path=path,
                request_id=request_id,
            )

            # Extract data from response (API may wrap in success/data)
            data = response.get("data", response)

            status_response: StepUpStatusResponse = {
                "status": data.get("status"),
                "tenantId": data.get("tenant_id") or data.get("tenantId") or self.tenant_id,
                "requestId": data.get("request_id") or data.get("requestId") or request_id,
                "decision": data.get("decision"),
                "reasonCodes": data.get("reason_codes") or data.get("reasonCodes"),
                "correlationId": data.get("correlation_id") or data.get("correlationId"),
                "expiresAtMs": data.get("expires_at_ms") or data.get("expiresAtMs"),
                "ttl": data.get("ttl"),
            }

            # Check if expired based on TTL
            now = now_epoch_seconds()
            if status_response.get("ttl") is not None and status_response["ttl"] <= now:
                status_response["status"] = "EXPIRED"

            return status_response

        except GateNotFoundError:
            raise
        except GateError as e:
            if e.code == "NOT_FOUND":
                raise GateNotFoundError(
                    f"Step-up request not found: {request_id}",
                    request_id=request_id,
                ) from e
            raise

    def await_decision(
        self,
        request_id: str,
        max_wait_ms: Optional[int] = None,
        interval_ms: Optional[int] = None,
    ) -> StepUpFinalResult:
        """
        Wait for step-up decision with polling.

        Polls until status is APPROVED, DENIED, or EXPIRED, or timeout is reached.

        Args:
            request_id: Step-up request ID
            max_wait_ms: Maximum wait time in milliseconds (default: from config)
            interval_ms: Polling interval in milliseconds (default: from config)

        Returns:
            Final step-up result

        Raises:
            GateNotFoundError: If request not found
            StepUpTimeoutError: If timeout exceeded
            GateError: For other errors
        """
        start_time = time.time() * 1000  # milliseconds
        max_wait = max_wait_ms or self.max_wait_ms
        interval = interval_ms or self.polling_interval_ms

        # Clamp interval to reasonable bounds (100ms - 2000ms)
        interval = clamp(interval, 100, 2000)

        while True:
            elapsed_ms = (time.time() * 1000) - start_time

            # Check timeout
            if elapsed_ms >= max_wait:
                raise StepUpTimeoutError(
                    f"Step-up decision timeout after {max_wait}ms",
                    request_id=request_id,
                )

            try:
                status = self.get_status(request_id)

                # Check if expired
                now = now_epoch_seconds()
                if status.get("ttl") is not None and status["ttl"] <= now:
                    return {
                        "status": "EXPIRED",
                        "requestId": request_id,
                        "elapsedMs": int(elapsed_ms),
                        "correlationId": status.get("correlationId"),
                    }

                # Check if decision reached
                status_val: StepUpStatus = status["status"]
                if status_val in ("APPROVED", "DENIED", "EXPIRED"):
                    return {
                        "status": status_val,
                        "requestId": request_id,
                        "elapsedMs": int(elapsed_ms),
                        "decision": status.get("decision"),
                        "reasonCodes": status.get("reasonCodes"),
                        "correlationId": status.get("correlationId"),
                    }

                # Status is PENDING, wait and poll again
                time.sleep(interval / 1000.0)

            except GateNotFoundError:
                raise  # Don't retry on NOT_FOUND
            except GateError as e:
                # For other errors, wait and retry
                remaining_ms = max_wait - int(elapsed_ms)
                if remaining_ms <= 0:
                    raise StepUpTimeoutError(
                        f"Step-up decision timeout after {max_wait}ms",
                        request_id=request_id,
                    ) from e

                time.sleep(min(interval / 1000.0, remaining_ms / 1000.0))

    def clamp_ttl(self, ttl_seconds: Optional[int]) -> int:
        """
        Clamp TTL to guardrails.

        Args:
            ttl_seconds: TTL in seconds (None for default)

        Returns:
            Clamped TTL in seconds
        """
        if ttl_seconds is None:
            return self.ttl_default_seconds
        return clamp(ttl_seconds, self.ttl_min_seconds, self.ttl_max_seconds)

