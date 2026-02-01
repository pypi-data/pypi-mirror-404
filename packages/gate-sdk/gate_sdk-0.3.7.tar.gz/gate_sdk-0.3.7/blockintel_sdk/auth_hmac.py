"""
HMAC v1 Authentication Provider

Provides HMAC v1 authentication for BlockIntel Gate SDK.

Canonical Request Format (v1):
v1\n
<http_method>\n
<path>\n
<tenant_id>\n
<key_id>\n
<timestamp_ms>\n
<nonce_or_empty>\n
<sha256_hex(body_json_canonical)>

Signature: base64(HMAC-SHA256(secret, canonical_request_string))
Header: x-blockintel-signature: v1=<base64_signature>
"""

import hmac
import hashlib
import time
import json
from typing import Dict, Any, Optional
from uuid import uuid4


class HmacAuthProvider:
    """
    HMAC v1 authentication provider for BlockIntel Gate.

    Signs requests using HMAC-SHA256 over a canonical request string (v1 format).
    """

    def __init__(
        self,
        tenant_id: str,
        key_id: str,
        hmac_secret: str,
        allowed_clock_skew_ms: int = 120000  # Default: 2 minutes
    ):
        """
        Initialize HMAC v1 auth provider.

        Args:
            tenant_id: Tenant ID
            key_id: Key ID (for key rotation support)
            hmac_secret: HMAC secret (plaintext, will be used to sign requests)
            allowed_clock_skew_ms: Allowed clock skew in milliseconds (default: 120000 = 2 minutes)
        """
        self.tenant_id = tenant_id
        self.key_id = key_id
        self.hmac_secret = hmac_secret.encode('utf-8') if isinstance(hmac_secret, str) else hmac_secret
        self.allowed_clock_skew_ms = allowed_clock_skew_ms

    def _canonicalize_json(self, obj: Any) -> str:
        """
        Canonicalize JSON by sorting keys recursively and removing whitespace.

        Args:
            obj: Object to canonicalize

        Returns:
            Canonical JSON string (no whitespace, sorted keys)
        """
        def sort_keys_recursive(item: Any) -> Any:
            if isinstance(item, dict):
                return {k: sort_keys_recursive(item[k]) for k in sorted(item.keys())}
            elif isinstance(item, list):
                return [sort_keys_recursive(i) for i in item]
            else:
                return item

        sorted_obj = sort_keys_recursive(obj)
        return json.dumps(sorted_obj, separators=(',', ':'))

    def _compute_body_hash(self, canonical_json: str) -> str:
        """
        Compute SHA256 hash of canonical JSON body.

        Args:
            canonical_json: Canonical JSON string

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def _build_canonical_request(
        self,
        method: str,
        path: str,
        tenant_id: str,
        key_id: str,
        timestamp_ms: int,
        nonce: Optional[str],
        body_hash: str
    ) -> str:
        """
        Build canonical request string (v1 format).

        Args:
            method: HTTP method (e.g., 'POST')
            path: Request path (e.g., '/defense/evaluate')
            tenant_id: Tenant ID
            key_id: Key ID
            timestamp_ms: Timestamp in milliseconds
            nonce: Optional nonce (UUID)
            body_hash: SHA256 hash of canonical JSON body

        Returns:
            Canonical request string
        """
        parts = [
            'v1',
            method,
            path,
            tenant_id,
            key_id,
            str(timestamp_ms),
            nonce or '',
            body_hash,
        ]
        return '\n'.join(parts)

    def apply_auth(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        method: str = 'POST',
        path: str = '/defense/evaluate',
        nonce: Optional[str] = None
    ) -> None:
        """
        Apply HMAC v1 authentication headers to the request.

        Args:
            headers: Request headers dictionary (modified in-place)
            payload: Request payload dictionary
            method: HTTP method (default: 'POST')
            path: Request path (default: '/defense/evaluate')
            nonce: Optional nonce for replay protection (default: None, will generate UUID if not provided)
        """
        # Generate request ID if not present
        request_id = payload.get('requestId') or str(uuid4())
        payload['requestId'] = request_id

        # Get timestamp in milliseconds (Unix epoch milliseconds)
        timestamp_ms = int(time.time() * 1000)

        # Ensure timestampMs is set in payload
        payload['timestampMs'] = timestamp_ms

        # Canonicalize JSON body (sort keys, no whitespace)
        canonical_json = self._canonicalize_json(payload)

        # Compute body hash
        body_hash = self._compute_body_hash(canonical_json)

        # Generate nonce if not provided
        if nonce is None:
            nonce = str(uuid4())

        # Build canonical request string
        canonical_request = self._build_canonical_request(
            method=method,
            path=path,
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            timestamp_ms=timestamp_ms,
            nonce=nonce,
            body_hash=body_hash
        )

        # Compute HMAC-SHA256 signature
        signature_bytes = hmac.new(
            self.hmac_secret,
            canonical_request.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Encode signature as base64
        import base64
        signature_base64 = base64.b64encode(signature_bytes).decode('utf-8')

        # Add headers (x-blockintel-* format)
        headers['x-blockintel-tenant-id'] = self.tenant_id
        headers['x-blockintel-key-id'] = self.key_id
        headers['x-blockintel-timestamp-ms'] = str(timestamp_ms)
        headers['x-blockintel-signature'] = f'v1={signature_base64}'
        
        # Add nonce header if provided
        if nonce:
            headers['x-blockintel-nonce'] = nonce

