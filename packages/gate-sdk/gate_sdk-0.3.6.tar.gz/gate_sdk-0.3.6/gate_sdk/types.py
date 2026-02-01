"""
Gate SDK - Type Definitions

Type definitions for Gate Hot Path API contracts.
"""

from typing import Literal, Optional, Dict, Any, TypedDict
from dataclasses import dataclass


# Decision types
GateDecision = Literal["ALLOW", "BLOCK", "REQUIRE_STEP_UP"]

# Step-up status types
StepUpStatus = Literal["PENDING", "APPROVED", "DENIED", "EXPIRED"]

# Gate Mode
GateMode = Literal["SHADOW", "ENFORCE"]

# Connection Failure Strategy
ConnectionFailureStrategy = Literal["FAIL_OPEN", "FAIL_CLOSED"]


# TransactionIntentV2 uses Dict[str, Any] because 'from' is a reserved keyword
# The API expects 'from' in the JSON, but we can't use it as a TypedDict field name
# Users should pass {'from': '0x...', 'to': '0x...', ...} directly
TransactionIntentV2 = Dict[str, Any]


class SigningContext(TypedDict, total=False):
    """Signing context metadata"""

    signerId: Optional[str]
    source: Optional[Dict[str, Any]]
    wallet: Optional[Dict[str, Any]]


class StepUpMetadata(TypedDict, total=False):
    """Step-up metadata in evaluate response"""

    requestId: str
    ttlSeconds: Optional[int]


class SimulationResult(TypedDict, total=False):
    """Simulation results (if simulation was enabled)"""

    willRevert: bool
    gasUsed: Optional[str]
    balanceChanges: Optional[list[Dict[str, Any]]]
    errorReason: Optional[str]


class DefenseEvaluateResponseV2(TypedDict, total=False):
    """Defense evaluate response (v2)"""

    decision: GateDecision
    reasonCodes: list[str]
    policyVersion: Optional[str]
    correlationId: Optional[str]
    stepUp: Optional[StepUpMetadata]
    enforced: Optional[bool]  # Whether the decision was enforced (false in SHADOW mode)
    shadowWouldBlock: Optional[bool]  # Whether shadow mode would have blocked
    mode: Optional[GateMode]  # Gate mode used for this evaluation
    simulation: Optional[SimulationResult]  # Simulation results (if simulation was enabled)
    simulationLatencyMs: Optional[int]  # Simulation latency in milliseconds (if simulation was enabled)


class StepUpStatusResponse(TypedDict, total=False):
    """Step-up status response"""

    status: StepUpStatus
    tenantId: str
    requestId: str
    decision: Optional[str]
    reasonCodes: Optional[list[str]]
    correlationId: Optional[str]
    expiresAtMs: Optional[int]
    ttl: Optional[int]


class StepUpFinalResult(TypedDict, total=False):
    """Final result from await_stepup_decision"""

    status: StepUpStatus
    requestId: str
    elapsedMs: int
    decision: Optional[str]
    reasonCodes: Optional[list[str]]
    correlationId: Optional[str]


# Fail-safe mode for SDK (deprecated - use onConnectionFailure instead)
FailSafeMode = Literal["ALLOW_ON_TIMEOUT", "BLOCK_ON_TIMEOUT", "BLOCK_ON_ANOMALY"]


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    trip_after_consecutive_failures: int = 5
    cool_down_ms: int = 30000  # 30 seconds

