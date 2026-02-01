"""
Gate SDK - Authentication

HMAC v1 signing and API key authentication for Gate Hot Path API.
"""

import hmac
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, Literal, Union
from dataclasses import dataclass

from .utils import canonical_json, sha256_hex


@dataclass(frozen=True)
class HmacAuth:
    """HMAC authentication configuration"""

    mode: Literal["hmac"]
    key_id: str
    secret: str


@dataclass(frozen=True)
class ApiKeyAuth:
    """API Key authentication configuration"""

    mode: Literal["apiKey"]
    api_key: str


Auth = Union[HmacAuth, ApiKeyAuth]


class HmacSigner:
    """
    HMAC v1 signer for Gate API requests.

    Signing Algorithm (v1):
    1. Create canonical signing string:
       v1\\n
       <HTTP_METHOD>\\n
       <PATH>\\n
       <TENANT_ID>\\n
       <KEY_ID>\\n
       <TIMESTAMP_MS>\\n
       <REQUEST_ID_AS_NONCE>\\n
       <SHA256_HEX_OF_BODY>

    2. Compute HMAC-SHA256(secret, signingString) as hex

    3. Include headers:
       - X-GATE-TENANT-ID
       - X-GATE-KEY-ID
       - X-GATE-TIMESTAMP-MS
       - X-GATE-REQUEST-ID (used as nonce in canonical string)
       - X-GATE-SIGNATURE (hex string)
    """

    def __init__(self, key_id: str, secret: str):
        """
        Initialize HMAC signer.

        Args:
            key_id: Key ID for key rotation support
            secret: HMAC secret (plaintext)
        """
        if not secret or len(secret) == 0:
            raise ValueError("HMAC secret cannot be empty")

        self.key_id = key_id
        self.secret = secret.encode("utf-8") if isinstance(secret, str) else secret

    def sign_request(
        self,
        method: str,
        path: str,
        tenant_id: str,
        timestamp_ms: int,
        request_id: str,
        body: Optional[Any] = None,
    ) -> Dict[str, str]:
        """
        Sign a request and return headers.

        Args:
            method: HTTP method (e.g., 'POST', 'GET')
            path: Request path (e.g., '/defense/evaluate')
            tenant_id: Tenant ID
            timestamp_ms: Timestamp in milliseconds
            request_id: Request ID (UUID)
            body: Request body (optional)

        Returns:
            Dictionary of headers to include in request
        """
        # Canonicalize body
        body_json_bytes = canonical_json(body) if body else b""
        body_hash = sha256_hex(body_json_bytes)

        # Construct canonical signing string (matches Hot Path format)
        signing_string = "\n".join([
            "v1",
            method.upper(),
            path,
            tenant_id,
            self.key_id,
            str(timestamp_ms),
            request_id,  # Used as nonce in canonical string
            body_hash,
        ])

        # Compute HMAC-SHA256 signature (returns hex)
        signature_bytes = hmac.new(
            self.secret,
            signing_string.encode("utf-8"),
            hashlib.sha256
        ).digest()
        signature = signature_bytes.hex()

        return {
            "X-GATE-TENANT-ID": tenant_id,
            "X-GATE-KEY-ID": self.key_id,
            "X-GATE-TIMESTAMP-MS": str(timestamp_ms),
            "X-GATE-REQUEST-ID": request_id,
            "X-GATE-SIGNATURE": signature,
        }


class ApiKeyAuthenticator:
    """API Key authenticator for Gate API requests"""

    def __init__(self, api_key: str):
        """
        Initialize API key authenticator.

        Args:
            api_key: API key string
        """
        if not api_key or len(api_key) == 0:
            raise ValueError("API key cannot be empty")

        self.api_key = api_key

    def create_headers(
        self,
        tenant_id: str,
        timestamp_ms: int,
        request_id: str,
    ) -> Dict[str, str]:
        """
        Create headers for API key authentication.

        Args:
            tenant_id: Tenant ID
            timestamp_ms: Timestamp in milliseconds
            request_id: Request ID

        Returns:
            Dictionary of headers to include in request
        """
        return {
            "X-API-KEY": self.api_key,
            "X-GATE-TENANT-ID": tenant_id,
            "X-GATE-REQUEST-ID": request_id,
            "X-GATE-TIMESTAMP-MS": str(timestamp_ms),
        }

