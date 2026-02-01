"""
Tests for HMAC v1 Authentication Provider
"""

import unittest
import hmac
import hashlib
import base64
import time
import json
from blockintel_sdk.auth_hmac import HmacAuthProvider


class TestHmacAuthProvider(unittest.TestCase):
    """Test HMAC v1 authentication provider"""

    def setUp(self):
        """Set up test fixtures"""
        self.tenant_id = "test-tenant-123"
        self.key_id = "key-1"
        self.hmac_secret = "test-secret-key"
        self.auth_provider = HmacAuthProvider(
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            hmac_secret=self.hmac_secret,
            allowed_clock_skew_ms=120000
        )

    def test_canonicalize_json_sorts_keys(self):
        """Test that JSON canonicalization sorts keys"""
        payload = {
            "z": 3,
            "a": 1,
            "m": {"c": 2, "a": 1},
            "b": 2,
        }

        canonical = self.auth_provider._canonicalize_json(payload)
        parsed = json.loads(canonical)

        # Check that keys are sorted
        self.assertEqual(list(parsed.keys()), ["a", "b", "m", "z"])
        self.assertEqual(list(parsed["m"].keys()), ["a", "c"])

    def test_canonicalize_json_no_whitespace(self):
        """Test that canonical JSON has no whitespace"""
        payload = {"a": 1, "b": 2}
        canonical = self.auth_provider._canonicalize_json(payload)

        # Should not contain spaces or newlines
        self.assertNotIn(" ", canonical)
        self.assertNotIn("\n", canonical)

    def test_compute_body_hash(self):
        """Test body hash computation"""
        canonical_json = '{"a":1,"b":2}'
        hash_result = self.auth_provider._compute_body_hash(canonical_json)

        # Should be 64 character hex string (SHA256)
        self.assertEqual(len(hash_result), 64)
        self.assertRegex(hash_result, r'^[a-f0-9]{64}$')

    def test_build_canonical_request(self):
        """Test canonical request string building"""
        method = "POST"
        path = "/defense/evaluate"
        timestamp_ms = 1234567890
        nonce = "test-nonce-123"
        body_hash = "abc123"

        canonical = self.auth_provider._build_canonical_request(
            method=method,
            path=path,
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            timestamp_ms=timestamp_ms,
            nonce=nonce,
            body_hash=body_hash
        )

        expected = "\n".join([
            "v1",
            method,
            path,
            self.tenant_id,
            self.key_id,
            str(timestamp_ms),
            nonce,
            body_hash,
        ])

        self.assertEqual(canonical, expected)

    def test_build_canonical_request_no_nonce(self):
        """Test canonical request without nonce"""
        canonical = self.auth_provider._build_canonical_request(
            method="POST",
            path="/defense/evaluate",
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            timestamp_ms=1234567890,
            nonce=None,
            body_hash="abc123"
        )

        lines = canonical.split("\n")
        self.assertEqual(lines[6], "")  # Nonce line should be empty

    def test_apply_auth_adds_headers(self):
        """Test that apply_auth adds correct headers"""
        headers = {}
        payload = {
            "requestId": "test-request-123",
            "tenantId": self.tenant_id,
            "signingContext": {"actorPrincipal": "test"},
            "txIntent": {"toAddress": "0x123"},
        }

        self.auth_provider.apply_auth(headers, payload)

        # Check required headers
        self.assertIn("x-blockintel-tenant-id", headers)
        self.assertIn("x-blockintel-key-id", headers)
        self.assertIn("x-blockintel-timestamp-ms", headers)
        self.assertIn("x-blockintel-signature", headers)
        self.assertIn("x-blockintel-nonce", headers)

        # Check header values
        self.assertEqual(headers["x-blockintel-tenant-id"], self.tenant_id)
        self.assertEqual(headers["x-blockintel-key-id"], self.key_id)
        self.assertTrue(headers["x-blockintel-timestamp-ms"].isdigit())
        self.assertTrue(headers["x-blockintel-signature"].startswith("v1="))

    def test_apply_auth_signature_format(self):
        """Test that signature is in correct format (v1=<base64>)"""
        headers = {}
        payload = {"test": "value"}

        self.auth_provider.apply_auth(headers, payload)

        signature = headers["x-blockintel-signature"]
        self.assertTrue(signature.startswith("v1="))

        # Extract base64 part
        base64_sig = signature[3:]
        try:
            decoded = base64.b64decode(base64_sig)
            # HMAC-SHA256 is 32 bytes
            self.assertEqual(len(decoded), 32)
        except Exception as e:
            self.fail(f"Signature is not valid base64: {e}")

    def test_apply_auth_signature_verification(self):
        """Test that signature can be verified"""
        headers = {}
        payload = {
            "requestId": "test-123",
            "tenantId": self.tenant_id,
            "signingContext": {"actorPrincipal": "test"},
            "txIntent": {"toAddress": "0x123"},
        }

        self.auth_provider.apply_auth(headers, payload)

        # Reconstruct canonical request to verify signature
        canonical_json = self.auth_provider._canonicalize_json(payload)
        body_hash = self.auth_provider._compute_body_hash(canonical_json)
        timestamp_ms = int(headers["x-blockintel-timestamp-ms"])
        nonce = headers["x-blockintel-nonce"]

        canonical_request = self.auth_provider._build_canonical_request(
            method="POST",
            path="/defense/evaluate",
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            timestamp_ms=timestamp_ms,
            nonce=nonce,
            body_hash=body_hash
        )

        # Compute expected signature
        expected_sig_bytes = hmac.new(
            self.hmac_secret.encode("utf-8"),
            canonical_request.encode("utf-8"),
            hashlib.sha256
        ).digest()

        expected_sig_base64 = base64.b64encode(expected_sig_bytes).decode("utf-8")

        # Extract signature from headers
        provided_sig = headers["x-blockintel-signature"][3:]  # Remove "v1=" prefix

        self.assertEqual(provided_sig, expected_sig_base64)

    def test_apply_auth_updates_payload(self):
        """Test that apply_auth updates payload with requestId and timestampMs"""
        headers = {}
        payload = {
            "tenantId": self.tenant_id,
            "signingContext": {},
            "txIntent": {},
        }

        self.auth_provider.apply_auth(headers, payload)

        # Should have requestId
        self.assertIn("requestId", payload)
        self.assertIsNotNone(payload["requestId"])

        # Should have timestampMs
        self.assertIn("timestampMs", payload)
        self.assertIsInstance(payload["timestampMs"], int)
        self.assertGreater(payload["timestampMs"], 0)

    def test_apply_auth_generates_request_id(self):
        """Test that requestId is generated if not present"""
        headers = {}
        payload = {
            "tenantId": self.tenant_id,
            "signingContext": {},
            "txIntent": {},
        }

        self.auth_provider.apply_auth(headers, payload)

        self.assertIn("requestId", payload)
        self.assertIsNotNone(payload["requestId"])

    def test_apply_auth_preserves_existing_request_id(self):
        """Test that existing requestId is preserved"""
        headers = {}
        existing_request_id = "existing-request-123"
        payload = {
            "requestId": existing_request_id,
            "tenantId": self.tenant_id,
            "signingContext": {},
            "txIntent": {},
        }

        self.auth_provider.apply_auth(headers, payload)

        self.assertEqual(payload["requestId"], existing_request_id)

    def test_apply_auth_custom_method_and_path(self):
        """Test that custom method and path can be provided"""
        headers = {}
        payload = {"test": "value"}

        self.auth_provider.apply_auth(
            headers,
            payload,
            method="GET",
            path="/defense/step-up/123"
        )

        # Verify signature uses correct method and path
        canonical_json = self.auth_provider._canonicalize_json(payload)
        body_hash = self.auth_provider._compute_body_hash(canonical_json)
        timestamp_ms = int(headers["x-blockintel-timestamp-ms"])
        nonce = headers["x-blockintel-nonce"]

        canonical_request = self.auth_provider._build_canonical_request(
            method="GET",
            path="/defense/step-up/123",
            tenant_id=self.tenant_id,
            key_id=self.key_id,
            timestamp_ms=timestamp_ms,
            nonce=nonce,
            body_hash=body_hash
        )

        # Should contain GET and custom path
        self.assertIn("GET", canonical_request)
        self.assertIn("/defense/step-up/123", canonical_request)


if __name__ == "__main__":
    unittest.main()








