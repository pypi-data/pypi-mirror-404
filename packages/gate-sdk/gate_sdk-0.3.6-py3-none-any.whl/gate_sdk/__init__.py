"""
BlockIntel Gate SDK for Python

Production-grade Python SDK for BlockIntel Gate Hot Path API.
"""

from .client import GateClient, GateClientConfig, StepUpConfig
from .auth import HmacAuth, ApiKeyAuth, Auth
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
    StepUpNotConfiguredError,
    StepUpTimeoutError,
    BlockIntelBlockedError,
    BlockIntelUnavailableError,
    BlockIntelAuthError,
    BlockIntelStepUpRequiredError,
)
from .types import (
    GateDecision,
    StepUpStatus,
    TransactionIntentV2,
    SigningContext,
    DefenseEvaluateResponseV2,
    StepUpStatusResponse,
    StepUpFinalResult,
    FailSafeMode,
    CircuitBreakerConfig,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitBreakerMetrics
from .metrics import MetricsCollector, Metrics
from .kms import wrap_kms_client, WrappedKmsClient, WrapKmsClientOptions
from .provenance import ProvenanceProvider, Provenance

__version__ = "0.3.6"

__all__ = [
    # Client
    "GateClient",
    "GateClientConfig",
    "StepUpConfig",
    # Auth
    "HmacAuth",
    "ApiKeyAuth",
    "Auth",
    # Errors
    "GateError",
    "GateNetworkError",
    "GateTimeoutError",
    "GateNotFoundError",
    "GateAuthError",
    "GateForbiddenError",
    "GateRateLimitError",
    "GateServerError",
    "GateInvalidResponseError",
    "StepUpNotConfiguredError",
    "StepUpTimeoutError",
    "BlockIntelBlockedError",
    "BlockIntelUnavailableError",
    "BlockIntelAuthError",
    "BlockIntelStepUpRequiredError",
    # Types
    "GateDecision",
    "StepUpStatus",
    "TransactionIntentV2",
    "SigningContext",
    "DefenseEvaluateResponseV2",
    "StepUpStatusResponse",
    "StepUpFinalResult",
    "FailSafeMode",
    "CircuitBreakerConfig",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitBreakerMetrics",
    # Metrics
    "MetricsCollector",
    "Metrics",
    # KMS Wrapper
    "wrap_kms_client",
    "WrappedKmsClient",
    "WrapKmsClientOptions",
    # Provenance Provider
    "ProvenanceProvider",
    "Provenance",
]

