"""
BlockIntel Gate Client

Main client for interacting with the BlockIntel Gate hot-path defense API.
"""

import time
import uuid
from typing import Optional, Dict, Any, Literal
from .auth import AuthProvider
from .exceptions import BlockIntelGateError, BlockIntelGateAuthError, BlockIntelGateDecisionError
import httpx


DecisionType = Literal["ALLOW", "BLOCK", "REQUIRE_STEP_UP"]
ReasonCode = Literal[
    "REPO_NOT_ALLOWLISTED",
    "WORKFLOW_NOT_ALLOWLISTED",
    "SIGNER_NOT_ALLOWLISTED",
    "REGION_ANOMALY",
    "IP_NOT_ALLOWLISTED",
    "TX_VALUE_EXCEEDS_THRESHOLD",
    "TO_ADDRESS_DENYLISTED",
    "NONCE_ANOMALY",
    "GAS_LIMIT_EXCEEDS_THRESHOLD",
    "MAX_FEE_PER_GAS_EXCEEDS_THRESHOLD",
    "DAILY_TX_COUNT_EXCEEDED",
    "DEFAULT_BLOCK",
    "POLICY_NOT_FOUND",
    "TENANT_NOT_FOUND",
]


class BlockIntelGateClient:
    """
    BlockIntel Gate Client

    Client for evaluating transactions against BlockIntel Gate policies.
    """

    def __init__(
        self,
        api_base_url: str,
        tenant_id: str,
        api_key: Optional[str] = None,
        auth_provider: Optional[AuthProvider] = None,
        timeout_seconds: int = 5,
    ):
        """
        Initialize the BlockIntel Gate client.

        Args:
            api_base_url: Base URL of the Gate API (e.g., "https://api.blockintelai.com")
            tenant_id: Tenant ID
            api_key: API key for authentication (optional if auth_provider is provided)
            auth_provider: Custom auth provider (optional)
            timeout_seconds: Request timeout in seconds
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.timeout_seconds = timeout_seconds
        self._auth_provider = auth_provider or (lambda: api_key) if api_key else None

        if not self._auth_provider:
            raise BlockIntelGateAuthError("Either api_key or auth_provider must be provided")

        self._sdk_name = "blockintel-python"
        self._sdk_version = "1.0.0"

    def evaluate(
        self,
        signing_context: Dict[str, Any],
        tx_intent: Dict[str, Any],
        request_id: Optional[str] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate a transaction intent against Gate policies.

        Args:
            signing_context: Signing context (actor, signer, source IP, GitHub info, etc.)
            tx_intent: Transaction intent (chain, to address, value, gas, etc.)
            request_id: Optional request ID (for idempotency). If not provided, a UUID is generated.
            simulate: If True, evaluate without persisting decision (dry-run mode)

        Returns:
            Decision response with decision, reasonCodes, policyVersion, etc.

        Raises:
            BlockIntelGateAuthError: If authentication fails
            BlockIntelGateDecisionError: If decision is BLOCK or REQUIRE_STEP_UP
            BlockIntelGateError: For other errors
        """
        if not request_id:
            request_id = str(uuid.uuid4())

        request_body = {
            "requestId": request_id,
            "tenantId": self.tenant_id,
            "timestampMs": int(time.time() * 1000),
            "signingContext": signing_context,
            "txIntent": tx_intent,
            "sdk": {
                "name": self._sdk_name,
                "version": self._sdk_version,
            },
        }

        # Build headers - support both API key and HMAC providers
        headers = {
            "Content-Type": "application/json",
        }

        # Check if auth_provider has apply_auth method (HMAC mode)
        if hasattr(self._auth_provider, 'apply_auth'):
            # HMAC v1 provider - calls apply_auth to add headers
            # Note: apply_auth modifies request_body to add/update requestId and timestampMs
            self._auth_provider.apply_auth(headers, request_body, method='POST', path='/defense/evaluate')
        else:
            # API key provider - callable that returns API key
            api_key = self._auth_provider()
            headers["Authorization"] = f"Bearer {api_key}"
            headers["X-API-Key"] = api_key

        # Add mode query parameter for simulation
        url = f"{self.api_base_url}/defense/evaluate"
        if simulate:
            url += "?mode=simulate"

        try:
            response = httpx.post(
                url,
                json=request_body,
                headers=headers,
                timeout=self.timeout_seconds,
            )

            if response.status_code == 401:
                raise BlockIntelGateAuthError("Authentication failed")

            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                error = result.get("error", {})
                raise BlockIntelGateError(
                    f"API error: {error.get('code', 'UNKNOWN')} - {error.get('message', 'Unknown error')}"
                )

            decision_data = result.get("data", {})
            decision = decision_data.get("decision")

            if decision == "BLOCK":
                reason_codes = decision_data.get("reasonCodes", [])
                raise BlockIntelGateDecisionError(
                    f"Transaction blocked: {', '.join(reason_codes)}",
                    decision_data,
                )
            elif decision == "REQUIRE_STEP_UP":
                raise BlockIntelGateDecisionError(
                    "Transaction requires step-up authentication",
                    decision_data,
                )

            return decision_data

        except httpx.TimeoutException:
            raise BlockIntelGateError("Request timeout")
        except httpx.RequestError as e:
            raise BlockIntelGateError(f"Request failed: {str(e)}")

    def wait_for_stepup_approval(
        self,
        request_id: str,
        timeout_seconds: int = 300,
        poll_interval_seconds: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Wait for a step-up request to be approved or denied.

        Polls the step-up request status until it's approved, denied, or expired,
        or until the timeout is reached.

        Args:
            request_id: The request ID from the REQUIRE_STEP_UP decision
            timeout_seconds: Maximum time to wait (default: 5 minutes)
            poll_interval_seconds: Time between polling attempts (default: 2 seconds)

        Returns:
            Step-up request status with approval/denial information

        Raises:
            BlockIntelGateError: If request not found, timeout exceeded, or request denied/expired
        """
        import time

        start_time = time.time()
        url = f"{self.api_base_url}/admin/gate/stepup/{self.tenant_id}/{request_id}"

        # Build headers for API key auth
        headers = {
            "Content-Type": "application/json",
        }

        if hasattr(self._auth_provider, 'apply_auth'):
            # HMAC provider - for admin endpoints, use API key if available
            # This is a simplified approach - in production, you might want separate admin auth
            pass
        else:
            api_key = self._auth_provider()
            headers["Authorization"] = f"Bearer {api_key}"
            headers["X-API-Key"] = api_key

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise BlockIntelGateError(
                    f"Timeout waiting for step-up approval (exceeded {timeout_seconds}s)"
                )

            try:
                response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    error = result.get("error", {})
                    if error.get("code") == "REQUEST_NOT_FOUND":
                        raise BlockIntelGateError(f"Step-up request {request_id} not found")
                    raise BlockIntelGateError(
                        f"API error: {error.get('code', 'UNKNOWN')} - {error.get('message', 'Unknown error')}"
                    )

                status_data = result.get("data", {})
                status = status_data.get("status")

                if status == "APPROVED":
                    return status_data
                elif status == "DENIED":
                    raise BlockIntelGateDecisionError(
                        f"Step-up request denied by {status_data.get('deniedBy', 'unknown')}",
                        status_data,
                    )
                elif status == "EXPIRED":
                    raise BlockIntelGateError("Step-up request expired")
                elif status == "PENDING":
                    # Continue polling
                    time.sleep(poll_interval_seconds)
                    continue
                else:
                    raise BlockIntelGateError(f"Unknown step-up status: {status}")

            except httpx.TimeoutException:
                raise BlockIntelGateError("Request timeout while polling step-up status")
            except httpx.RequestError as e:
                raise BlockIntelGateError(f"Request failed: {str(e)}")
            except BlockIntelGateDecisionError:
                raise  # Re-raise decision errors
            except BlockIntelGateError:
                raise  # Re-raise gate errors

    def guarded_sign_and_send(
        self,
        signing_context: Dict[str, Any],
        tx_intent: Dict[str, Any],
        sign_fn: callable,
        send_fn: Optional[callable] = None,
    ) -> Any:
        """
        Evaluate, sign, and send a transaction (if allowed).

        This is a convenience method that:
        1. Calls evaluate() to check if the transaction is allowed
        2. If ALLOW: signs the transaction using sign_fn
        3. If send_fn is provided: sends the signed transaction
        4. Returns the signed transaction (or send result if send_fn is provided)

        Args:
            signing_context: Signing context
            tx_intent: Transaction intent
            sign_fn: Function to sign the transaction. Called with tx_intent as argument.
            send_fn: Optional function to send the signed transaction. Called with signed_tx as argument.

        Returns:
            Signed transaction (if send_fn is None) or send result (if send_fn is provided)

        Raises:
            BlockIntelGateDecisionError: If transaction is blocked or requires step-up
            BlockIntelGateError: For other errors
        """
        # Evaluate first
        self.evaluate(signing_context, tx_intent)

        # If we get here, transaction is allowed - proceed with signing
        signed_tx = sign_fn(tx_intent)

        if send_fn:
            return send_fn(signed_tx)

        return signed_tx

