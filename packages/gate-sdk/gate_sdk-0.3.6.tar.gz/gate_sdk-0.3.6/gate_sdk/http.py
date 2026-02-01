"""
Gate SDK - HTTP Client

HTTP client with timeout, retry, and error handling.
"""

import httpx
from typing import Dict, Any, Optional, TypeVar
from urllib.parse import urlparse

from .errors import (
    GateError,
    GateNetworkError,
    GateTimeoutError,
    GateNotFoundError,
    GateAuthError,
    GateForbiddenError,
    GateRateLimitError,
    GateServerError,
    GateInvalidResponseError,
)
from .retry import retry_with_backoff, is_retryable_status, is_retryable_error

T = TypeVar("T")


class HttpClient:
    """HTTP client with retry and timeout support"""

    def __init__(
        self,
        base_url: str,
        timeout_ms: int = 15000,
        user_agent: Optional[str] = None,
        max_attempts: int = 3,
        base_delay_ms: int = 100,
        max_delay_ms: int = 800,
        factor: float = 2.0,
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL of the API
            timeout_ms: Request timeout in milliseconds
            user_agent: User agent string
            max_attempts: Maximum retry attempts
            base_delay_ms: Base delay for exponential backoff
            max_delay_ms: Maximum delay for exponential backoff
            factor: Exponential backoff factor
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = timeout_ms
        self.user_agent = user_agent or "blockintel-gate-sdk/0.1.0"
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.factor = factor

        # Validate HTTPS in production (allow http only for localhost)
        parsed = urlparse(self.base_url)
        if parsed.scheme == "http" and "localhost" not in parsed.netloc:
            import os
            if os.getenv("NODE_ENV") == "production":
                raise ValueError("base_url must use HTTPS in production (except localhost)")

        # Create httpx client
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_ms / 1000.0),
            headers={"User-Agent": self.user_agent},
        )

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry and timeout.

        Args:
            method: HTTP method (e.g., 'POST', 'GET')
            path: Request path (e.g., '/defense/evaluate')
            headers: Request headers
            body: Request body (will be JSON encoded)
            request_id: Request ID for error tracking

        Returns:
            Response JSON as dictionary

        Raises:
            GateError: For API errors
        """
        url = f"{self.base_url}{path}"
        headers = headers or {}
        headers["Content-Type"] = "application/json"

        def make_request() -> Dict[str, Any]:
            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                )

                # Parse JSON response first (needed for error code extraction)
                data = None
                try:
                    data = response.json()
                except Exception as parse_error:
                    # If we can't parse JSON, still try to create error with status code
                    if not response.is_success:
                        text = response.text[:512] if response.text else ""
                        raise self._status_to_error(response, request_id, {"body_snippet": text})
                    raise GateInvalidResponseError(
                        f"Failed to parse JSON response: {str(parse_error)}",
                        status_code=response.status_code,
                        details={"body_snippet": text},
                        request_id=request_id,
                    ) from parse_error

                # Check for errors (now we have parsed data for error code extraction)
                if not response.is_success:
                    # Check for retryable status codes
                    if not is_retryable_status(response.status_code):
                        # Debug: log the response data structure for 403 errors
                        if response.status_code == 403:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.debug('[HTTP CLIENT] 403 error response data', {
                                'data': data,
                                'data_type': type(data).__name__,
                                'has_error_key': 'error' in (data or {}),
                                'error_obj': data.get('error') if data else None,
                            })
                        raise self._status_to_error(response, request_id, data)

                return data

            except httpx.TimeoutException as e:
                raise GateTimeoutError(
                    f"Request timeout after {self.timeout_ms}ms",
                    request_id=request_id,
                ) from e
            except httpx.NetworkError as e:
                raise GateNetworkError(
                    f"Network error: {str(e)}",
                    request_id=request_id,
                ) from e
            except GateError:
                raise  # Re-raise GateError as-is
            except Exception as e:
                if is_retryable_error(e):
                    raise  # Re-raise retryable errors for retry logic
                raise GateNetworkError(
                    f"Unexpected error: {str(e)}",
                    request_id=request_id,
                ) from e

        # Retry with backoff
        try:
            return retry_with_backoff(
                make_request,
                max_attempts=self.max_attempts,
                base_delay_ms=self.base_delay_ms,
                max_delay_ms=self.max_delay_ms,
                factor=self.factor,
            )
        except GateError:
            raise  # Re-raise GateError as-is
        except Exception as e:
            if isinstance(e, GateError):
                raise
            raise GateNetworkError(
                f"Request failed after {self.max_attempts} attempts: {str(e)}",
                request_id=request_id,
            ) from e

    def _status_to_error(
        self,
        response: httpx.Response,
        request_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> GateError:
        """
        Map HTTP status code to GateError.

        Args:
            response: HTTP response
            request_id: Request ID
            data: Response JSON data (if available)

        Returns:
            Appropriate GateError subclass
        """
        correlation_id = response.headers.get("X-Correlation-ID")

        if response.status_code == 401:
            return GateAuthError(
                "Authentication failed",
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
            )
        elif response.status_code == 403:
            # Extract error code from response data if available
            # Hot Path returns: {success: false, error: {code: "...", message: "...", ...}}
            error_code = None
            error_message = "Access forbidden"
            if data:
                # Check nested error object first (Hot Path format)
                error_obj = data.get("error")
                if isinstance(error_obj, dict):
                    error_code = error_obj.get("code") or error_obj.get("errorCode") or error_obj.get("error_code")
                    error_message = error_obj.get("message") or error_obj.get("error") or error_message
                # Fallback to top-level fields
                if not error_code:
                    error_code = data.get("code") or data.get("errorCode") or data.get("error_code")
                if error_message == "Access forbidden":
                    error_message = data.get("message") or data.get("error") or error_message
            # Debug: log the extracted error code (can be removed later)
            import logging
            logger = logging.getLogger(__name__)
            logger.debug('[HTTP CLIENT] 403 error response', {
                'error_code': error_code,
                'error_message': error_message,
                'data_keys': list(data.keys()) if data else [],
                'has_error_obj': 'error' in (data or {}),
            })
            return GateForbiddenError(
                error_message,
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
                code=error_code or "FORBIDDEN",
            )
        elif response.status_code == 404:
            return GateNotFoundError(
                "Resource not found",
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
            )
        elif response.status_code == 429:
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass
            return GateRateLimitError(
                "Rate limit exceeded",
                retry_after=retry_after,
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
            )
        elif 500 <= response.status_code < 600:
            return GateServerError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
            )
        else:
            return GateError(
                f"HTTP {response.status_code}: {response.reason_phrase}",
                status_code=response.status_code,
                code="NETWORK_ERROR",
                request_id=request_id,
                correlation_id=correlation_id,
                details=data or {},
            )

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

