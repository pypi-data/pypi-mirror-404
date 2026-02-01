"""
Gate SDK - Heartbeat Manager

Manages heartbeat token acquisition and validation.
Heartbeat tokens prove Gate is alive and enforcing policy.
Required for all signing operations.

Features:
- Automatic refresh with jitter
- Exponential backoff on failures
- Client instance metadata tracking
"""

import time
import threading
import random
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .http import HttpClient
from .errors import GateError, GateAuthError


@dataclass
class HeartbeatToken:
    """Heartbeat token with expiration"""
    token: str
    expires_at: int  # Unix timestamp (seconds)
    jti: Optional[str] = None  # JWT ID (for reference)
    policy_hash: Optional[str] = None  # Policy hash (for reference)


class HeartbeatManager:
    """Manages heartbeat token acquisition and refresh"""

    def __init__(
        self,
        http_client: HttpClient,
        tenant_id: str,
        signer_id: str,
        environment: str = "prod",
        refresh_interval_seconds: int = 10,
        client_instance_id: Optional[str] = None,
        sdk_version: Optional[str] = None,
        api_key: Optional[str] = None,  # Optional API key for heartbeat auth
    ):
        """
        Initialize heartbeat manager.

        Args:
            http_client: HTTP client for API calls
            tenant_id: Tenant ID
            signer_id: Signer ID (e.g., "kms:alias/prod-signer")
            environment: Environment (default: "prod")
            refresh_interval_seconds: How often to refresh heartbeat (default: 10s)
            client_instance_id: Unique client instance ID (auto-generated if not provided)
            sdk_version: SDK version for tracking (default: "1.0.0")
            api_key: Optional API key for heartbeat authentication
        """
        self._http_client = http_client
        self._tenant_id = tenant_id
        self._signer_id = signer_id
        self._environment = environment
        self._base_refresh_interval = refresh_interval_seconds
        self._client_instance_id = client_instance_id or str(uuid.uuid4())
        self._sdk_version = sdk_version or "1.0.0"

        self._current_token: Optional[HeartbeatToken] = None
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False
        self._consecutive_failures = 0
        self._max_backoff_seconds = 30
        self._api_key = api_key

    def start(self, wait_for_initial: bool = True) -> None:
        """
        Start background heartbeat refresher
        
        Args:
            wait_for_initial: If True, wait for initial heartbeat to be acquired before returning.
                             This ensures heartbeat is available for first sign() call.
        """
        if self._started:
            return

        self._started = True
        self._stop_event.clear()

        # Acquire initial heartbeat synchronously (critical for first sign() call)
        if wait_for_initial:
            max_retries = 5
            retry_delay = 0.5  # seconds
            heartbeat_acquired = False
            for attempt in range(max_retries):
                try:
                    print(f"[HEARTBEAT] Attempting to acquire initial heartbeat (attempt {attempt + 1}/{max_retries})...")
                    self._acquire_heartbeat()
                    # Small delay to ensure token is set in the lock
                    time.sleep(0.1)
                    # Verify token is actually available
                    token = self.get_token()
                    if token:
                        print(f"[HEARTBEAT] Initial heartbeat acquired successfully (token length: {len(token)})")
                        heartbeat_acquired = True
                        break
                    else:
                        print(f"[HEARTBEAT] Heartbeat token acquired but get_token() returned None, retrying...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[HEARTBEAT] Failed to acquire initial heartbeat (attempt {attempt + 1}/{max_retries}): {e}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                    else:
                        print(f"[HEARTBEAT] Failed to acquire initial heartbeat after {max_retries} attempts: {e}")
                        print(f"[HEARTBEAT] Will continue in background thread - sign() calls may fail until heartbeat is acquired")
                        # Don't fail hard - will retry in background thread
            
            if not heartbeat_acquired:
                print(f"[HEARTBEAT] WARNING: Initial heartbeat not acquired - sign() calls will fail until heartbeat is available")
        else:
            # Non-blocking mode (for backward compatibility)
            try:
                self._acquire_heartbeat()
            except Exception as e:
                print(f"[HEARTBEAT] Failed to acquire initial heartbeat: {e}")

        # Start background refresh thread
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()

    def stop(self) -> None:
        """Stop background heartbeat refresher"""
        if not self._started:
            return

        self._started = False
        self._stop_event.set()

        if self._refresh_thread:
            self._refresh_thread.join(timeout=1.0)

    def get_token(self) -> Optional[str]:
        """
        Get current heartbeat token if valid.

        Returns:
            Heartbeat token string, or None if missing/expired
        """
        with self._lock:
            if not self._current_token:
                return None

            # Check expiration (with 2 second buffer)
            now = int(time.time())
            if self._current_token.expires_at <= (now + 2):
                return None

            return self._current_token.token

    def is_valid(self) -> bool:
        """Check if current heartbeat token is valid"""
        return self.get_token() is not None

    def update_signer_id(self, signer_id: str) -> None:
        """Update signer ID (called when signer is known)"""
        # Normalize signer_id to handle alias/ prefix differences
        # 'alias/gate-canary-trading-bot' and 'gate-canary-trading-bot' should be treated as the same
        normalized_new = signer_id.replace("alias/", "") if signer_id.startswith("alias/") else signer_id
        with self._lock:
            normalized_old = self._signer_id.replace("alias/", "") if self._signer_id.startswith("alias/") else self._signer_id
            if normalized_old != normalized_new:
                old_signer_id = self._signer_id
                # Use the normalized version (without alias/) for consistency
                self._signer_id = normalized_new
                # Only invalidate token if signer_id actually changed (not just format difference)
                if normalized_old != 'unknown' and self._current_token:
                    print(f"[HEARTBEAT] Signer ID changed from '{old_signer_id}' to '{signer_id}' (normalized: '{normalized_new}') - invalidating token")
                    self._current_token = None
                elif normalized_old == 'unknown' and not self._current_token:
                    # First time setting signer_id, but no token yet - try to acquire immediately
                    print(f"[HEARTBEAT] Signer ID set to '{signer_id}' (normalized: '{normalized_new}', was 'unknown') - will acquire token on next refresh")
            elif self._signer_id != signer_id:
                # Same normalized ID but different format - just update the stored format, don't invalidate
                self._signer_id = normalized_new
                print(f"[HEARTBEAT] Signer ID format updated (same ID): '{signer_id}' -> '{normalized_new}' (token remains valid)")

    def _acquire_heartbeat(self) -> None:
        """Acquire a new heartbeat token from Control Plane. NEVER logs token value (security)"""
        try:
            with self._lock:
                signer_id = self._signer_id
                client_instance_id = self._client_instance_id
                sdk_version = self._sdk_version
                
            # Heartbeat endpoint accepts x-gate-heartbeat-key header (required - no fallbacks)
            headers = {}
            if not self._api_key:
                raise ValueError(
                    "Heartbeat API key is required. GATE_HEARTBEAT_KEY must be set in environment or passed to HeartbeatManager."
                )
            headers["x-gate-heartbeat-key"] = self._api_key
            
            response = self._http_client.request(
                method="POST",
                path="/api/v1/gate/heartbeat",
                headers=headers,
                body={
                    "tenantId": self._tenant_id,
                    "signerId": signer_id,
                    "environment": self._environment,
                    "clientInstanceId": client_instance_id,
                    "sdkVersion": sdk_version,
                },
            )

            if response.get("success"):
                data = response.get("data", {})
                token = data.get("heartbeatToken")
                expires_at = data.get("expiresAt")
                jti = data.get("jti")
                policy_hash = data.get("policyHash")

                if not token or not expires_at:
                    raise GateError("Invalid heartbeat response: missing token or expiresAt")

                with self._lock:
                    self._current_token = HeartbeatToken(
                        token=token,
                        expires_at=expires_at,
                        jti=jti,
                        policy_hash=policy_hash,
                    )

                # Log WITHOUT token value (security)
                print(f"[HEARTBEAT] Acquired heartbeat token", {
                    "expires_at": expires_at,
                    "jti": jti,
                    "policy_hash": policy_hash[:8] + "..." if policy_hash else None,
                    # DO NOT log token value
                })
            else:
                error = response.get("error", {})
                raise GateError(f"Heartbeat acquisition failed: {error.get('message', 'Unknown error')}")

        except Exception as e:
            # Log error but NEVER log token
            print(f"[HEARTBEAT] Failed to acquire heartbeat: {str(e)}")
            raise

    def get_client_instance_id(self) -> str:
        """Get client instance ID (for tracking)"""
        return self._client_instance_id

    def _refresh_loop(self) -> None:
        """Background loop to refresh heartbeat tokens with jitter and backoff"""
        while not self._stop_event.is_set():
            try:
                # Calculate interval with jitter and backoff
                base_interval = self._base_refresh_interval
                jitter = random.uniform(0, 2)  # 0-2 seconds jitter
                backoff = self._calculate_backoff()
                interval = base_interval + jitter + backoff

                # Wait for refresh interval (with jitter and backoff)
                if self._stop_event.wait(interval):
                    break  # Stop event set

                # Acquire new heartbeat
                self._acquire_heartbeat()
                # Success - reset failure count
                with self._lock:
                    self._consecutive_failures = 0

            except Exception as e:
                # Failure - increment and retry
                with self._lock:
                    self._consecutive_failures += 1
                # Log error but continue - existing token remains valid until expiry
                print(f"[HEARTBEAT] Refresh failed (will retry): {e}")
                # Continue with existing token if available

    def _calculate_backoff(self) -> float:
        """Calculate exponential backoff (capped at max_backoff_seconds)"""
        if self._consecutive_failures == 0:
            return 0.0

        # Exponential backoff: 2^failures seconds, capped at max_backoff_seconds
        backoff_seconds = min(
            (2 ** self._consecutive_failures),
            self._max_backoff_seconds
        )

        return backoff_seconds


def require_heartbeat(func):
    """
    Decorator to require valid heartbeat before executing function.

    Usage:
        @require_heartbeat
        def sign(...):
            ...
    """
    def wrapper(self, *args, **kwargs):
        # Check if heartbeat manager exists and has valid token
        if hasattr(self, '_heartbeat_manager'):
            token = self._heartbeat_manager.get_token()
            if not token:
                raise GateError(
                    "HEARTBEAT_MISSING",
                    "Signing blocked: Heartbeat token is missing or expired. Gate must be alive and enforcing policy."
                )
        else:
            # No heartbeat manager - fail hard
            raise GateError(
                "HEARTBEAT_MISSING",
                "Signing blocked: Heartbeat manager not initialized. Gate heartbeat is required."
            )

        return func(self, *args, **kwargs)
    return wrapper

