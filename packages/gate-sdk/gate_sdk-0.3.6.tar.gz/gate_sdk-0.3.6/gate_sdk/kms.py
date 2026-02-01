"""
Gate SDK - KMS Wrapper

Wraps boto3 KMS client to intercept sign() calls and enforce Gate policies.
"""

import hashlib
from typing import Dict, Any, Optional, Callable, Literal, Union
from types import MethodType

from .client import GateClient
from .errors import (
    BlockIntelBlockedError,
    BlockIntelStepUpRequiredError,
    GateError,
)


class WrapKmsClientOptions:
    """KMS wrapper options"""

    def __init__(
        self,
        mode: Literal["enforce", "dry-run"] = "enforce",
        on_decision: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        extract_tx_intent: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        additional_signing_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize wrapper options.

        Args:
            mode: Wrapper mode ("enforce" or "dry-run")
            on_decision: Callback invoked when a decision is made
            extract_tx_intent: Custom hook to extract transaction intent from sign params
            additional_signing_context: Additional fields to merge into signingContext (e.g., run_id)
        """
        self.mode = mode
        self.on_decision = on_decision or (lambda decision, details: None)
        self.extract_tx_intent = extract_tx_intent or default_extract_tx_intent
        self.additional_signing_context = additional_signing_context or {}


class WrappedKmsClient:
    """Wrapped KMS client that enforces Gate policies"""

    def __init__(
        self,
        original_client: Any,  # boto3.client("kms")
        gate_client: GateClient,
        options: WrapKmsClientOptions,
    ):
        """
        Initialize wrapped KMS client.

        Args:
            original_client: Original boto3 KMS client
            gate_client: Gate client for evaluation
            options: Wrapper options
        """
        self._original_client = original_client
        self._gate_client = gate_client
        self._options = options

        # Preserve all original client methods and attributes
        for attr_name in dir(original_client):
            if not attr_name.startswith("_") and attr_name != "sign":
                try:
                    attr_value = getattr(original_client, attr_name)
                    if not callable(attr_value) or isinstance(attr_value, MethodType):
                        setattr(self, attr_name, attr_value)
                except AttributeError:
                    pass

    def sign(self, **kwargs) -> Dict[str, Any]:
        """
        Intercept sign() call and evaluate with Gate before forwarding to KMS.

        Args:
            **kwargs: KMS sign() parameters (KeyId, Message, MessageType, SigningAlgorithm)

        Returns:
            KMS sign response

        Raises:
            BlockIntelBlockedError: If Gate blocks the transaction
            BlockIntelStepUpRequiredError: If step-up is required
        """
        return self._handle_sign_call(kwargs)

    def _handle_sign_call(self, sign_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle intercepted sign() call"""

        # Extract transaction intent
        tx_intent = self._options.extract_tx_intent(sign_params)

        # Extract signer ID from KeyId
        # Normalize KeyId to match heartbeat signer_id format (remove 'alias/' prefix if present)
        key_id = sign_params.get("KeyId", "unknown")
        # Normalize: 'alias/gate-canary-trading-bot' -> 'gate-canary-trading-bot'
        # This ensures heartbeat signer_id matches what we use here
        signer_id = key_id.replace("alias/", "") if key_id.startswith("alias/") else key_id

        # Update heartbeat manager with actual signer_id from KeyId
        # This may invalidate the current token if signer_id changed
        # Skip if heartbeat manager is None (local mode)
        heartbeat_token = None
        if self._gate_client._heartbeat_manager is not None:
            self._gate_client._heartbeat_manager.update_signer_id(signer_id)
            # Get heartbeat token (if available) - but don't block here
            # Let the Hot Path handle heartbeat validation to ensure decisions are saved
            heartbeat_token = self._gate_client._heartbeat_manager.get_token()
        
        # Debug logging for heartbeat token in KMS wrapper
        import logging
        logger = logging.getLogger(__name__)
        if heartbeat_token:
            logger.debug(f'[KMS WRAPPER] Heartbeat token available for sign() call (length={len(heartbeat_token)})')
        else:
            # More detailed logging to understand why token is None
            logger.warning('[KMS WRAPPER] No heartbeat token available for sign() call', extra={
                'has_heartbeat_manager': self._gate_client._heartbeat_manager is not None,
                'heartbeat_manager_started': self._gate_client._heartbeat_manager._started if self._gate_client._heartbeat_manager else False,
                'has_current_token': self._gate_client._heartbeat_manager._current_token is not None if self._gate_client._heartbeat_manager else False,
                'signer_id': signer_id,
            })

        # Build signing context
        signing_context = {
            "signerId": signer_id,
            "actorPrincipal": "kms-signer",  # Default
            **({"heartbeatToken": heartbeat_token} if heartbeat_token else {}),  # Attach heartbeat token if available
            **self._options.additional_signing_context,  # Merge additional fields (e.g., run_id)
        }
        
        # Log signing context for debugging
        logger.debug(f'[KMS WRAPPER] Signing context prepared: hasHeartbeatToken={bool(signing_context.get("heartbeatToken"))}, signerId={signer_id}')

        try:
            # Call Gate evaluate() with correct signature for gate_sdk
            # gate_sdk.evaluate() expects: evaluate(req={'txIntent': ..., 'signingContext': ...}, request_id=None)
            decision = self._gate_client.evaluate(
                {
                    "txIntent": tx_intent,
                    "signingContext": signing_context,
                },
                None,  # request_id (optional, None = auto-generate)
            )

            # Decision is ALLOW (evaluate() doesn't throw)
            self._options.on_decision("ALLOW", {"decision": decision, "signerId": signer_id, "params": sign_params})

            if self._options.mode == "dry-run":
                # Dry-run mode: evaluate but still allow
                return self._original_client.sign(**sign_params)

            # Enforce mode: forward to real KMS
            return self._original_client.sign(**sign_params)

        except BlockIntelBlockedError as error:
            # Gate blocked the transaction
            self._options.on_decision("BLOCK", {"error": error, "signerId": signer_id, "params": sign_params})
            raise

        except BlockIntelStepUpRequiredError as error:
            # Step-up required
            self._options.on_decision(
                "REQUIRE_STEP_UP", {"error": error, "signerId": signer_id, "params": sign_params}
            )
            raise

        except Exception as error:
            # Other errors (network, auth, etc.) - re-raise
            raise


def default_extract_tx_intent(sign_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default transaction intent extraction from KMS sign parameters.

    Extracts minimal txIntent from KMS sign params:
    - Uses Message hash as payloadHash
    - Sets networkFamily to 'OTHER' (unknown)
    - Sets signerId from KeyId
    """
    message = sign_params.get("Message")
    if message is None:
        return {
            "networkFamily": "OTHER",
            "toAddress": None,
            "payloadHash": None,
            "dataHash": None,
        }

    # Compute SHA256 hash of message
    if isinstance(message, bytes):
        message_bytes = message
    elif isinstance(message, str):
        message_bytes = message.encode("utf-8")
    else:
        # Try to convert to bytes
        message_bytes = bytes(message)

    message_hash = hashlib.sha256(message_bytes).hexdigest()

    return {
        "networkFamily": "OTHER",
        "toAddress": None,  # Unknown from KMS message alone
        "payloadHash": message_hash,
        "dataHash": message_hash,  # Backward compatibility
    }


def wrap_kms_client(
    kms_client: Any,  # boto3.client("kms")
    gate_client: GateClient,
    options: Optional[WrapKmsClientOptions] = None,
) -> WrappedKmsClient:
    """
    Wrap boto3 KMS client to intercept sign() calls.

    Args:
        kms_client: boto3 KMS client instance
        gate_client: Gate client for evaluation
        options: Wrapper options (optional)

    Returns:
        Wrapped KMS client that enforces Gate policies

    Example:
        ```python
        import boto3
        from gate_sdk import GateClient, wrap_kms_client

        kms = boto3.client("kms")
        gate = GateClient(
            base_url=os.getenv("GATE_BASE_URL"),
            tenant_id=os.getenv("GATE_TENANT_ID"),
            auth={"mode": "hmac", "key_id": os.getenv("GATE_KEY_ID"), "secret": os.getenv("GATE_HMAC_SECRET")},
        )

        protected_kms = wrap_kms_client(kms, gate)

        # Now calls to protected_kms.sign(...) will be intercepted
        result = protected_kms.sign(
            KeyId="alias/my-key",
            Message=b"...",
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )
        ```
    """
    if options is None:
        options = WrapKmsClientOptions()

    return WrappedKmsClient(kms_client, gate_client, options)


