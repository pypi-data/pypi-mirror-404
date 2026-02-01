"""
Gate SDK - Gate Client

Main client for interacting with Gate Hot Path API.
"""

import uuid
import time
import asyncio
from typing import Dict, Any, Optional, Literal, Union, Callable, List
from dataclasses import dataclass, field

from .auth import HmacAuth, ApiKeyAuth, Auth, HmacSigner, ApiKeyAuthenticator
from .http import HttpClient
from .stepup import StepUpPoller, DEFAULT_POLLING_INTERVAL_MS, DEFAULT_MAX_WAIT_MS
from .heartbeat import HeartbeatManager
from .types import (
    DefenseEvaluateResponseV2,
    GateDecision,
    StepUpStatusResponse,
    StepUpFinalResult,
    FailSafeMode,
    CircuitBreakerConfig,
    GateMode,
    ConnectionFailureStrategy,
)
from .errors import (
    GateError,
    GateAuthError,
    GateForbiddenError,
    GateRateLimitError,
    StepUpNotConfiguredError,
    BlockIntelBlockedError,
    BlockIntelUnavailableError,
    BlockIntelAuthError,
    BlockIntelStepUpRequiredError,
    GateTimeoutError,
    GateNetworkError,
    GateServerError,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .metrics import MetricsCollector, Metrics
from .utils import now_ms
from .provenance import ProvenanceProvider
from .security import IamPermissionRiskChecker, IamPermissionRiskCheckerOptions


@dataclass
class StepUpConfig:
    """Step-up configuration"""

    polling_interval_ms: int = DEFAULT_POLLING_INTERVAL_MS
    max_wait_ms: int = DEFAULT_MAX_WAIT_MS
    treat_require_stepup_as_block_when_disabled: bool = True


@dataclass
class GateClientConfig:
    """Gate client configuration"""

    base_url: str
    tenant_id: str
    auth: Auth
    timeout_ms: int = 50  # Default: 50ms (target for hot path)
    user_agent: Optional[str] = None
    clock_skew_ms: int = 120000
    retries: int = 1  # Max retry attempts (default: 1)
    fail_safe_mode: FailSafeMode = "ALLOW_ON_TIMEOUT"  # Deprecated - use onConnectionFailure
    mode: Optional[GateMode] = None  # Default: SHADOW (can be overridden by env var GATE_MODE)
    on_connection_failure: Optional[ConnectionFailureStrategy] = None  # Default: based on mode
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    enable_stepup: bool = False
    stepup: StepUpConfig = field(default_factory=StepUpConfig)
    on_metrics: Optional[Callable[[Any], None]] = None  # Metrics hook
    signer_id: Optional[str] = None  # Signer ID for heartbeat (if known upfront)
    heartbeat_refresh_interval_seconds: int = 10  # How often to refresh heartbeat (default: 10s)
    breakglass_token: Optional[str] = None  # Break-glass token for emergency override
    local: bool = False  # Local development mode (disables auth, heartbeat, break-glass)
    enforcement_mode: Optional[Literal['SOFT', 'HARD']] = None  # Default: SOFT
    allow_insecure_kms_sign_permission: Optional[bool] = None  # Default: True in SOFT, False in HARD
    kms_key_ids: Optional[List[str]] = None  # Optional: specific KMS keys to check


class GateClient:
    """Gate Client for Hot Path API"""

    def __init__(self, config: GateClientConfig):
        """
        Initialize Gate client.

        Args:
            config: Client configuration
        """
        self.config = config
        
        # Determine mode: env var > config > default (SHADOW for safety)
        import os
        env_mode = os.getenv("GATE_MODE")
        self._mode: GateMode = env_mode or config.mode or "SHADOW"
        
        # Determine connection failure strategy: config > default based on mode
        if config.on_connection_failure:
            self._on_connection_failure: ConnectionFailureStrategy = config.on_connection_failure
        else:
            # Default: FAIL_OPEN in SHADOW mode, FAIL_CLOSED in ENFORCE mode
            self._on_connection_failure = "FAIL_OPEN" if self._mode == "SHADOW" else "FAIL_CLOSED"

        # Initialize auth
        if config.auth.mode == "hmac":
            self._hmac_signer = HmacSigner(
                key_id=config.auth.key_id,
                secret=config.auth.secret,
            )
            self._api_key_auth = None
        else:
            self._hmac_signer = None
            self._api_key_auth = ApiKeyAuthenticator(api_key=config.auth.api_key)

        # Initialize HTTP client
        self._http_client = HttpClient(
            base_url=config.base_url,
            timeout_ms=config.timeout_ms,
            user_agent=config.user_agent,
        )

        # Initialize step-up poller if enabled
        self._stepup_poller: Optional[StepUpPoller] = None
        if config.enable_stepup:
            self._stepup_poller = StepUpPoller(
                http_client=self._http_client,
                tenant_id=config.tenant_id,
                polling_interval_ms=config.stepup.polling_interval_ms,
                max_wait_ms=config.stepup.max_wait_ms,
            )

        # Initialize circuit breaker if configured
        self._circuit_breaker: Optional[CircuitBreaker] = None
        if config.circuit_breaker:
            from .circuit_breaker import CircuitBreaker as CB
            self._circuit_breaker = CB(config.circuit_breaker)

        # Initialize metrics collector
        self._metrics = MetricsCollector()
        if config.on_metrics:
            self._metrics.register_hook(config.on_metrics)

        # Initialize heartbeat manager (required for signing)
        # Use control plane URL for heartbeat (different from hot path base_url)
        # Prefer GATE_CONTROL_PLANE_URL environment variable, then config, then extract from base_url
        import os
        control_plane_url = os.getenv("GATE_CONTROL_PLANE_URL")
        if not control_plane_url:
            # Try config if explicitly set
            if hasattr(config, 'control_plane_url') and config.control_plane_url:
                control_plane_url = config.control_plane_url
            else:
                # Extract control plane URL from base_url (remove /defense if present)
                control_plane_url = config.base_url
                if '/defense' in control_plane_url:
                    control_plane_url = control_plane_url.split('/defense')[0]
            
        # Create heartbeat HTTP client with same auth as main client
        heartbeat_http_client = HttpClient(
            base_url=control_plane_url,
            timeout_ms=5000,  # 5s timeout for heartbeat
            user_agent=config.user_agent,
        )
        # Note: Heartbeat endpoint accepts X-API-KEY header
        # We'll pass API key via environment variable or use HMAC if needed
        # Initialize heartbeat manager with configured signer_id if provided
        # Otherwise, use placeholder - will be updated when signer is known from signing operations
        initial_signer_id = config.signer_id or 'unknown'
        # Initialize heartbeat manager (skip in local mode)
        if config.local:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('[GATE CLIENT] LOCAL MODE ENABLED - Auth, heartbeat, and break-glass are disabled')
            self._heartbeat_manager = None
        else:
            # Get heartbeat key for heartbeat auth (required - no fallbacks for production)
            import os
            heartbeat_api_key = os.getenv("GATE_HEARTBEAT_KEY")
            if not heartbeat_api_key:
                raise ValueError(
                    "GATE_HEARTBEAT_KEY environment variable is required for heartbeat authentication. "
                    "Set GATE_HEARTBEAT_KEY in your environment or ECS task definition."
                )
            
            self._heartbeat_manager = HeartbeatManager(
                http_client=heartbeat_http_client,
                tenant_id=config.tenant_id,
                signer_id=initial_signer_id,
                environment=getattr(config, 'environment', 'prod'),
                refresh_interval_seconds=config.heartbeat_refresh_interval_seconds,
                api_key=heartbeat_api_key,
            )
            # Start heartbeat refresher (automatically sends heartbeats in background)
            # Wait for initial heartbeat to be acquired (critical for first sign() call)
            print("[GATE CLIENT] Starting heartbeat manager and waiting for initial heartbeat...")
            self._heartbeat_manager.start(wait_for_initial=True)
            print("[GATE CLIENT] Heartbeat manager started")

        # Perform IAM permission risk check (skip in local mode)
        if not config.local:
            enforcement_mode = config.enforcement_mode or 'SOFT'
            allow_insecure_kms_sign_permission = (
                config.allow_insecure_kms_sign_permission
                if config.allow_insecure_kms_sign_permission is not None
                else (enforcement_mode == 'SOFT')
            )

            risk_checker = IamPermissionRiskChecker(
                IamPermissionRiskCheckerOptions(
                    tenant_id=config.tenant_id,
                    signer_id=config.signer_id,
                    environment=getattr(config, 'environment', None),
                    enforcement_mode=enforcement_mode,
                    allow_insecure_kms_sign_permission=allow_insecure_kms_sign_permission,
                    kms_key_ids=config.kms_key_ids,
                )
            )

            # Perform synchronous risk check first (blocks in HARD mode if risk detected)
            # This ensures HARD mode can block initialization synchronously
            risk_checker.check_sync()

            # Perform async IAM simulation check in background (non-blocking)
            # This provides higher confidence detection but doesn't block initialization
            # In HARD mode, if async check finds risk, it will log but won't block (already initialized)
            # Use threading to run async check without blocking
            import threading
            def run_async_check():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._perform_iam_risk_check_async(risk_checker, enforcement_mode))
                    loop.close()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning('[GATE CLIENT] Async IAM risk check thread error: %s', str(e))
            
            thread = threading.Thread(target=run_async_check, daemon=True)
            thread.start()

    async def _perform_iam_risk_check_async(
        self,
        risk_checker: IamPermissionRiskChecker,
        enforcement_mode: Literal['SOFT', 'HARD'],
    ) -> None:
        """
        Perform async IAM permission risk check (non-blocking)

        Performs async IAM simulation check in background.
        Logs warnings but doesn't block (initialization already completed).
        """
        try:
            # This will perform async IAM simulation check
            # Note: check_sync() already ran and blocked if needed in HARD mode
            # This async check provides additional confidence but doesn't block initialization
            await risk_checker.check()
        except Exception as e:
            # Log but don't raise (initialization already succeeded)
            # The sync check already handled blocking in HARD mode
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('[GATE CLIENT] Async IAM risk check warning: %s', str(e))

    def evaluate(
        self,
        req: Dict[str, Any],
        request_id: Optional[str] = None,
        simulate: bool = False,
    ) -> DefenseEvaluateResponseV2:
        """
        Evaluate a transaction defense request.

        Implements:
        - Circuit breaker protection
        - Fail-safe modes (ALLOW_ON_TIMEOUT, BLOCK_ON_TIMEOUT, BLOCK_ON_ANOMALY)
        - Metrics collection
        - Error handling (BLOCK → BlockIntelBlockedError, REQUIRE_STEP_UP → BlockIntelStepUpRequiredError)

        Args:
            req: Request dictionary with 'txIntent' and optional 'signingContext'
            request_id: Optional request ID (generated if not provided)

        Returns:
            Defense evaluate response

        Raises:
            BlockIntelBlockedError: If transaction is BLOCKED
            BlockIntelStepUpRequiredError: If step-up is required
            BlockIntelAuthError: If authentication fails (always fail CLOSED)
            BlockIntelUnavailableError: If service is unavailable and fail-safe is BLOCK_ON_TIMEOUT
            GateError: For other API errors
        """
        if not request_id:
            request_id = str(uuid.uuid4())

        timestamp_ms = req.get("timestampMs") or now_ms()
        start_time = int(time.time() * 1000)
        fail_safe_mode = self.config.fail_safe_mode or "ALLOW_ON_TIMEOUT"

        # Wrap request with circuit breaker if enabled
        def execute_request() -> DefenseEvaluateResponseV2:
            # Get heartbeat token if available (but don't block here - let Hot Path handle validation)
            # This ensures decisions are always saved to DynamoDB even when heartbeat fails
            heartbeat_token = None
            if not self.config.local and self._heartbeat_manager:
                heartbeat_token = self._heartbeat_manager.get_token()
                # Don't raise error here - let Hot Path handle heartbeat validation
                # This ensures decisions are saved to DynamoDB for UI visibility

            # Prepare signing context
            signing_context = req.get("signingContext") or req.get("signing_context") or {}
            
            # Only include heartbeat token if it's valid (not None)
            # Including None would change the canonical JSON hash
            if heartbeat_token:
                signing_context["heartbeatToken"] = heartbeat_token

            # Inject provenance from environment if available
            provenance = ProvenanceProvider.get_provenance()
            if provenance:
                if "caller" not in signing_context:
                    signing_context["caller"] = {}
                signing_context["caller"].update(provenance.to_dict())

            # Determine mode for this request (request-level override > client-level > default)
            request_mode: GateMode = req.get("mode") or self._mode
            
            # Add break-glass token if configured (skip in local mode)
            if not self.config.local and self.config.breakglass_token:
                signing_context["breakglassToken"] = self.config.breakglass_token
            
            # Prepare request body (camelCase for API - API expects camelCase, not snake_case)
            # Note: API also requires 'sdk' field with name and version
            body = {
                "tenantId": self.config.tenant_id,
                "txIntent": req.get("txIntent") or req.get("tx_intent"),
                "signingContext": signing_context,
                "requestId": request_id,
                "timestampMs": timestamp_ms,
                "sdk": {
                    "name": "gate-sdk",
                    "version": "0.1.0",
                },
                "mode": request_mode,
                "onConnectionFailure": self._on_connection_failure,
            }
            
            # Add simulation flag if requested
            if simulate:
                body["simulate"] = True

            # Prepare headers (skip auth in local mode)
            headers: Dict[str, str] = {}

            if self.config.local:
                # Local mode: no auth headers, just basic headers
                headers = {
                    'Content-Type': 'application/json',
                }
                import logging
                logger = logging.getLogger(__name__)
                logger.info('[GATE CLIENT] LOCAL MODE - Skipping authentication')
            elif self._hmac_signer:
                hmac_headers = self._hmac_signer.sign_request(
                    method="POST",
                    path="/defense/evaluate",
                    tenant_id=self.config.tenant_id,
                    timestamp_ms=timestamp_ms,
                    request_id=request_id,
                    body=body,
                )
                headers.update(hmac_headers)
            elif self._api_key_auth:
                api_key_headers = self._api_key_auth.create_headers(
                    tenant_id=self.config.tenant_id,
                    timestamp_ms=timestamp_ms,
                    request_id=request_id,
                )
                headers.update(api_key_headers)
            else:
                raise GateError("No authentication configured")

            # Make request (API returns snake_case, convert to camelCase)
            response = self._http_client.request(
                method="POST",
                path="/defense/evaluate",
                headers=headers,
                body=body,
                request_id=request_id,
            )

            # Extract data from response (API may wrap in success/data)
            data = response.get("data", response)

            # Extract simulation results from metadata if present
            metadata = data.get("metadata") or {}
            simulation_data = metadata.get("simulation")
            
            # Convert snake_case to camelCase
            result: DefenseEvaluateResponseV2 = {
                "decision": data.get("decision"),
                "reasonCodes": data.get("reason_codes") or data.get("reasonCodes") or [],
                "policyVersion": data.get("policy_version") or data.get("policyVersion"),
                "correlationId": data.get("correlation_id") or data.get("correlationId"),
                "enforced": data.get("enforced", request_mode == "ENFORCE"),
                "shadowWouldBlock": data.get("shadow_would_block") or data.get("shadowWouldBlock", False),
                "mode": data.get("mode") or request_mode,
            }
            
            # Add simulation results if available
            if simulation_data:
                result["simulation"] = {
                    "willRevert": simulation_data.get("will_revert") or simulation_data.get("willRevert", False),
                    "gasUsed": simulation_data.get("gas_used") or simulation_data.get("gasUsed"),
                    "balanceChanges": simulation_data.get("balance_changes") or simulation_data.get("balanceChanges"),
                    "errorReason": simulation_data.get("error_reason") or simulation_data.get("errorReason"),
                }
                result["simulationLatencyMs"] = metadata.get("simulation_latency_ms") or metadata.get("simulationLatencyMs")

            # Handle step-up metadata
            step_up_data = data.get("step_up") or data.get("stepUp")
            if step_up_data:
                result["stepUp"] = {
                    "requestId": step_up_data.get("request_id") or step_up_data.get("requestId") or "",
                    "ttlSeconds": step_up_data.get("ttl_seconds") or step_up_data.get("ttlSeconds"),
                }

            latency_ms = int(time.time() * 1000) - start_time

            # Handle decision types
            if result["decision"] == "BLOCK":
                # In SHADOW mode, log but don't throw - always allow
                if request_mode == "SHADOW":
                    # Log shadow block event
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "[GATE SHADOW MODE] Would have blocked transaction",
                        extra={
                            "request_id": request_id,
                            "reason_codes": result["reasonCodes"],
                            "correlation_id": result["correlationId"],
                            "tenant_id": self.config.tenant_id,
                            "signer_id": req.get("signingContext", {}).get("signerId"),
                        }
                    )
                    
                    # Record metrics (always, not just when on_metrics hook is set)
                    self._metrics.record_request("WOULD_BLOCK", latency_ms)
                    
                    # Return ALLOW with shadowWouldBlock flag
                    return {
                        **result,
                        "decision": "ALLOW",
                        "enforced": False,
                        "shadowWouldBlock": True,
                    }
                
                # ENFORCE mode: BLOCK → throw BlockIntelBlockedError
                receipt_id = data.get("decision_id") or request_id
                reason_codes = result.get("reasonCodes", [])
                reason_code = reason_codes[0] if reason_codes else "POLICY_VIOLATION"
                self._metrics.record_request("BLOCK", latency_ms)
                raise BlockIntelBlockedError(
                    reason_code=reason_code,
                    receipt_id=receipt_id,
                    correlation_id=result.get("correlationId"),
                    request_id=request_id,
                    reasonCodes=reason_codes,  # Pass full array of reason codes
                )

            if result["decision"] == "REQUIRE_STEP_UP":
                # REQUIRE_STEP_UP handling
                if self.config.enable_stepup and self._stepup_poller and result.get("stepUp"):
                    # Step-up is enabled - throw BlockIntelStepUpRequiredError
                    step_up_request_id = result["stepUp"]["requestId"] or request_id
                    expires_at_ms = step_up_data.get("expires_at_ms") if step_up_data else None
                    status_url = f"/defense/stepup/status?tenantId={self.config.tenant_id}&requestId={step_up_request_id}"
                    self._metrics.record_request("REQUIRE_STEP_UP", latency_ms)
                    raise BlockIntelStepUpRequiredError(
                        step_up_request_id=step_up_request_id,
                        status_url=status_url,
                        expires_at_ms=expires_at_ms,
                        request_id=request_id,
                    )
                else:
                    # Step-up not enabled - treat as BLOCK
                    receipt_id = data.get("decision_id") or request_id
                    reason_code = "STEPUP_REQUIRED"
                    reason_codes = result.get("reasonCodes", [reason_code])
                    self._metrics.record_request("BLOCK", latency_ms)
                    raise BlockIntelBlockedError(
                        reason_code=reason_code,
                        receipt_id=receipt_id,
                        correlation_id=result.get("correlationId"),
                        request_id=request_id,
                        reasonCodes=reason_codes,  # Pass full array of reason codes
                    )

            # ALLOW - record metrics and return
            self._metrics.record_request("ALLOW", latency_ms)
            return result

        # Execute with circuit breaker if enabled
        try:
            if self._circuit_breaker:
                return self._circuit_breaker.execute(execute_request)
            return execute_request()
        except CircuitBreakerOpenError as error:
            self._metrics.record_circuit_breaker_open()
            fail_safe_result = self._handle_fail_safe(fail_safe_mode, error, request_id)
            if fail_safe_result:
                return fail_safe_result
            raise error
        except (GateAuthError, GateForbiddenError) as error:
            # Handle auth failures (401/403) - check if it's a heartbeat-related error
            # Heartbeat failures should be treated as BLOCK, not auth errors
            error_code = error.code or ""
            error_details = error.details or {}
            # Check nested error object (Hot Path format: {success: false, error: {code: "...", ...}})
            error_obj = error_details.get("error") or {}
            if isinstance(error_obj, dict):
                error_code_from_details = error_obj.get("code") or error_obj.get("errorCode") or ""
            else:
                error_code_from_details = error_details.get("code") or error_details.get("errorCode") or ""
            
            # Debug logging (can be removed later)
            import logging
            logger = logging.getLogger(__name__)
            logger.debug('[GATE CLIENT] Error handling', {
                'error_code': error_code,
                'error_code_from_details': error_code_from_details,
                'error_message': error.message,
                'error_details_keys': list(error_details.keys()) if error_details else [],
            })
            
            # Check if this is a heartbeat-related error (should be treated as BLOCK)
            heartbeat_error_codes = [
                "HEARTBEAT_MISSING",
                "HEARTBEAT_ENFORCEMENT_FAILURE",
                "HEARTBEAT_EXPIRED",
                "HEARTBEAT_INVALID",
            ]
            
            is_heartbeat_error = (
                any(code in error_code.upper() for code in heartbeat_error_codes) or
                any(code in error_code_from_details.upper() for code in heartbeat_error_codes) or
                any(code in error.message.upper() for code in heartbeat_error_codes)
            )
            
            if is_heartbeat_error:
                # Heartbeat failure = BLOCK transaction
                reason_code = error_code_from_details or error_code or "HEARTBEAT_MISSING"
                reason_codes = [reason_code]
                self._metrics.record_request("BLOCK", 0)  # Latency not available for errors
                raise BlockIntelBlockedError(
                    reason_code=reason_code,
                    receipt_id=request_id,  # Use request_id as receipt_id if decision_id not available
                    correlation_id=error.correlation_id,
                    request_id=request_id,
                    reasonCodes=reason_codes,
                )
            
            # True auth failures (401/403) - always fail CLOSED (BLOCK)
            self._metrics.record_error()
            status_code = error.status_code or 401
            raise BlockIntelAuthError(
                message=error.message,
                status_code=status_code,
                request_id=request_id,
            )
        except (GateTimeoutError, GateServerError, GateNetworkError, BlockIntelUnavailableError) as error:
            # Handle connection failures (timeout, network errors, 5xx)
            self._metrics.record_timeout() if isinstance(error, GateTimeoutError) else self._metrics.record_error()

            # Apply connection failure strategy
            if self._on_connection_failure == "FAIL_OPEN":
                # FAIL_OPEN: Allow transaction, log critical event. Degraded (logs/telemetry only; never in HTTP request).
                import logging
                _dl = logging.getLogger(__name__)
                _dl.error(
                    "[GATE CONNECTION FAILURE] FAIL_OPEN mode - allowing transaction",
                    extra={
                        "request_id": request_id,
                        "error": str(error),
                        "tenant_id": self.config.tenant_id,
                        "mode": self._mode,
                    }
                )
                _dl.warning("[GATE SDK] X-BlockIntel-Degraded: true (reason: fail_open)")

                # Record FAIL_OPEN metric
                self._metrics.record_request("FAIL_OPEN", int(time.time() * 1000) - start_time)

                return {
                    "decision": "ALLOW",
                    "reasonCodes": ["GATE_HOTPATH_UNAVAILABLE"],
                    "correlationId": request_id,
                    "enforced": False,
                    "mode": self._mode,
                }
            else:
                # FAIL_CLOSED: Block transaction
                raise BlockIntelUnavailableError(
                    message=f"Signing blocked: Gate hot path unreachable (fail-closed). {error}",
                    request_id=request_id,
                )
        except GateRateLimitError as error:
            # 429: log degraded, then re-raise
            import logging
            logging.getLogger(__name__).warning("[GATE SDK] X-BlockIntel-Degraded: true (reason: 429)")
            raise
        except (BlockIntelBlockedError, BlockIntelStepUpRequiredError):
            # Re-throw BlockIntelBlockedError and BlockIntelStepUpRequiredError as-is
            raise
        except Exception as error:
            # Other errors - record and re-throw
            self._metrics.record_error()
            raise error

    def _handle_fail_safe(
        self,
        mode: FailSafeMode,
        error: Exception,
        request_id: str,
    ) -> Optional[DefenseEvaluateResponseV2]:
        """
        Handle fail-safe modes for timeouts/errors.

        Args:
            mode: Fail-safe mode
            error: The error that occurred
            request_id: Request ID

        Returns:
            Fail-safe response if mode allows, None otherwise
        """
        if mode == "ALLOW_ON_TIMEOUT":
            # Trading bots: ALLOW on timeout with degraded flag (logs/telemetry only; never in HTTP request)
            import logging
            logging.getLogger(__name__).warning("[GATE SDK] X-BlockIntel-Degraded: true (reason: fail_safe_allow)")
            return {
                "decision": "ALLOW",
                "reasonCodes": ["FAIL_SAFE_ALLOW"],
                "correlationId": request_id,
            }

        if mode == "BLOCK_ON_TIMEOUT":
            # Fail CLOSED - don't return, let error propagate
            return None

        if mode == "BLOCK_ON_ANOMALY":
            # BLOCK only on explicit BLOCK/REQUIRE_STEP_UP decisions, not network hiccups
            # On timeout: ALLOW gracefully (logs/telemetry only; never in HTTP request)
            import logging
            logging.getLogger(__name__).warning("[GATE SDK] X-BlockIntel-Degraded: true (reason: fail_safe_allow)")
            return {
                "decision": "ALLOW",
                "reasonCodes": ["FAIL_SAFE_ALLOW"],
                "correlationId": request_id,
            }

        return None

    def get_metrics(self):
        """Get current metrics"""
        return self._metrics.get_metrics()

    def get_circuit_breaker_metrics(self):
        """Get circuit breaker metrics (if enabled)"""
        return self._circuit_breaker.get_metrics() if self._circuit_breaker else None

    def get_stepup_status(
        self,
        request_id: str,
        tenant_id: Optional[str] = None,
    ) -> StepUpStatusResponse:
        """
        Get step-up status.

        Args:
            request_id: Step-up request ID
            tenant_id: Optional tenant ID (default: from config)

        Returns:
            Step-up status response

        Raises:
            StepUpNotConfiguredError: If step-up not enabled
            GateError: For other errors
        """
        if not self._stepup_poller:
            raise StepUpNotConfiguredError(request_id=request_id)

        tenant_id = tenant_id or self.config.tenant_id
        poller = StepUpPoller(
            http_client=self._http_client,
            tenant_id=tenant_id,
            polling_interval_ms=self.config.stepup.polling_interval_ms,
            max_wait_ms=self.config.stepup.max_wait_ms,
        )

        return poller.get_status(request_id)

    def await_stepup_decision(
        self,
        request_id: str,
        max_wait_ms: Optional[int] = None,
        interval_ms: Optional[int] = None,
    ) -> StepUpFinalResult:
        """
        Wait for step-up decision with polling.

        Args:
            request_id: Step-up request ID
            max_wait_ms: Maximum wait time in milliseconds (default: from config)
            interval_ms: Polling interval in milliseconds (default: from config)

        Returns:
            Final step-up result

        Raises:
            StepUpNotConfiguredError: If step-up not enabled
            GateError: For other errors
        """
        if not self._stepup_poller:
            raise StepUpNotConfiguredError(request_id=request_id)

        return self._stepup_poller.await_decision(
            request_id,
            max_wait_ms=max_wait_ms or self.config.stepup.max_wait_ms,
            interval_ms=interval_ms or self.config.stepup.polling_interval_ms,
        )

    def wrap_kms_client(
        self,
        kms_client: Any,  # boto3.client("kms")
        mode: Literal["enforce", "dry-run"] = "enforce",
        on_decision: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        extract_tx_intent: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        """
        Wrap boto3 KMS client to intercept sign() calls.

        Args:
            kms_client: boto3 KMS client instance
            mode: Wrapper mode ("enforce" or "dry-run")
            on_decision: Callback invoked when a decision is made
            extract_tx_intent: Custom hook to extract transaction intent from sign params

        Returns:
            Wrapped KMS client that enforces Gate policies

        Example:
            ```python
            import boto3

            kms = boto3.client("kms")
            protected_kms = gate_client.wrap_kms_client(kms)

            # Now SignCommand calls will be intercepted and evaluated by Gate
            result = protected_kms.sign(
                KeyId="alias/my-key",
                Message=b"...",
                MessageType="RAW",
                SigningAlgorithm="ECDSA_SHA_256",
            )
            ```
        """
        from .kms import wrap_kms_client, WrapKmsClientOptions

        options = WrapKmsClientOptions(
            mode=mode,
            on_decision=on_decision,
            extract_tx_intent=extract_tx_intent,
        )
        return wrap_kms_client(kms_client, self, options)

    def close(self) -> None:
        """Close the HTTP client"""
        self._http_client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

