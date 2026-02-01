"""
Gate SDK - Exception Classes

Custom exceptions for Gate SDK errors.
"""

from typing import Optional, Dict, Any


class GateError(Exception):
    """Base exception for Gate SDK errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
        self.request_id = request_id
        self.correlation_id = correlation_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"[{self.code}]")
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "code": self.code or "UNKNOWN",
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }


class GateNetworkError(GateError):
    """Network error (connection failed, timeout, etc.)"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="NETWORK_ERROR", **kwargs)


class GateTimeoutError(GateError):
    """Request timeout"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="TIMEOUT", **kwargs)


class GateNotFoundError(GateError):
    """Resource not found (404)"""

    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, status_code=404, code="NOT_FOUND", **kwargs)


class GateAuthError(GateError):
    """Authentication error (401/403)"""

    def __init__(self, message: str = "Authentication failed", status_code: int = 401, **kwargs):
        super().__init__(message, status_code=status_code, code="UNAUTHORIZED", **kwargs)


class GateForbiddenError(GateError):
    """Access forbidden (403)"""

    def __init__(self, message: str = "Access forbidden", code: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=403, code=code or "FORBIDDEN", **kwargs)


class GateRateLimitError(GateError):
    """Rate limit exceeded (429)"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, status_code=429, code="RATE_LIMITED", **kwargs)
        self.retry_after = retry_after


class GateServerError(GateError):
    """Server error (5xx)"""

    def __init__(self, message: str = "Server error", status_code: int = 500, **kwargs):
        super().__init__(message, status_code=status_code, code="SERVER_ERROR", **kwargs)


class GateInvalidResponseError(GateError):
    """Invalid response format"""

    def __init__(self, message: str = "Invalid response format", **kwargs):
        super().__init__(message, code="INVALID_RESPONSE", **kwargs)


class StepUpNotConfiguredError(GateError):
    """Step-up is required but not configured in SDK"""

    def __init__(self, request_id: Optional[str] = None):
        super().__init__(
            "Step-up is required but not configured in SDK. Enable step-up in client config or treat REQUIRE_STEP_UP as BLOCK.",
            code="STEP_UP_NOT_CONFIGURED",
            request_id=request_id,
        )


class StepUpTimeoutError(GateError):
    """Step-up polling timeout"""

    def __init__(self, message: str = "Step-up decision timeout", **kwargs):
        super().__init__(message, code="STEP_UP_TIMEOUT", **kwargs)


class BlockIntelBlockedError(GateError):
    """Transaction blocked by Gate"""

    def __init__(
        self,
        reason_code: str = "POLICY_VIOLATION",  # Default to POLICY_VIOLATION if not provided
        receipt_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        reasonCodes: Optional[list[str]] = None,  # Full array of reason codes
        message: Optional[str] = None,  # Optional message (for backward compatibility - overrides default message)
    ):
        # Use provided message or construct from reason_code
        error_message = message or f"Transaction blocked: {reason_code}"
        
        super().__init__(
            error_message,
            code="BLOCKED",
            details={"reason_code": reason_code, "receipt_id": receipt_id},
            correlation_id=correlation_id,
            request_id=request_id,
        )
        self.receipt_id = receipt_id
        self.reason_code = reason_code  # First reason code (for backward compatibility)
        self.reasonCodes = reasonCodes or [reason_code]  # Full array of reason codes


class BlockIntelUnavailableError(GateError):
    """Service unavailable error"""

    def __init__(self, message: str, request_id: Optional[str] = None):
        super().__init__(message, code="SERVICE_UNAVAILABLE", request_id=request_id)


class BlockIntelAuthError(GateError):
    """Auth error - always fails CLOSED (never silently allows)"""

    def __init__(self, message: str, status_code: int, request_id: Optional[str] = None):
        code = "UNAUTHORIZED" if status_code == 401 else "FORBIDDEN"
        super().__init__(message, status_code=status_code, code=code, request_id=request_id)


class BlockIntelStepUpRequiredError(GateError):
    """Step-up required error"""

    def __init__(
        self,
        step_up_request_id: str,
        status_url: Optional[str] = None,
        expires_at_ms: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(
            "Step-up approval required",
            code="STEP_UP_NOT_CONFIGURED",
            details={
                "step_up_request_id": step_up_request_id,
                "status_url": status_url,
                "expires_at_ms": expires_at_ms,
            },
            request_id=request_id,
        )
        self.step_up_request_id = step_up_request_id
        self.status_url = status_url
        self.expires_at_ms = expires_at_ms

