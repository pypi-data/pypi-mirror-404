"""
Tests for HMAC v1 Signer

Golden vector tests for canonical JSON and HMAC signing.
"""

import pytest
import hmac
import hashlib
from gate_sdk.auth import HmacSigner
from gate_sdk.utils import canonical_json, sha256_hex


class TestCanonicalJson:
    """Test canonical JSON serialization"""

    def test_sorts_keys(self):
        """Test that JSON canonicalization sorts keys"""
        obj = {"z": 3, "a": 1, "m": {"c": 2, "a": 1}, "b": 2}
        canonical = canonical_json(obj)
        parsed = eval(canonical.decode("utf-8").replace("true", "True").replace("false", "False").replace("null", "None"))

        # Check that keys are sorted
        assert list(parsed.keys()) == ["a", "b", "m", "z"]
        assert list(parsed["m"].keys()) == ["a", "c"]

    def test_no_whitespace(self):
        """Test that canonical JSON has no whitespace"""
        obj = {"a": 1, "b": 2}
        canonical = canonical_json(obj).decode("utf-8")

        # Should not contain spaces or newlines
        assert " " not in canonical
        assert "\n" not in canonical

    def test_deterministic(self):
        """Test that canonical JSON is deterministic"""
        obj = {
            "tx_intent": {
                "from": "0x123",
                "to": "0x456",
                "value": "1000000000000000000",
            },
            "signing_context": {"signerId": "test-signer"},
        }

        result1 = canonical_json(obj)
        result2 = canonical_json(obj)

        # Should be identical
        assert result1 == result2


class TestSha256Hex:
    """Test SHA256 hash computation"""

    def test_deterministic(self):
        """Test that SHA256 is deterministic"""
        input_str = "test-input"
        hash1 = sha256_hex(input_str)
        hash2 = sha256_hex(input_str)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex is 64 chars

    def test_different_inputs(self):
        """Test that different inputs produce different hashes"""
        hash1 = sha256_hex("input1")
        hash2 = sha256_hex("input2")

        assert hash1 != hash2


class TestHmacSigner:
    """Test HMAC v1 signer"""

    def test_creates_signer(self):
        """Test that signer can be created"""
        signer = HmacSigner(key_id="test-key", secret="test-secret")
        assert signer.key_id == "test-key"

    def test_rejects_empty_secret(self):
        """Test that empty secret is rejected"""
        with pytest.raises(ValueError, match="secret cannot be empty"):
            HmacSigner(key_id="test", secret="")

    def test_produces_deterministic_signature(self):
        """Test that signature is deterministic"""
        signer = HmacSigner(key_id="test-key", secret="test-secret")

        params = {
            "method": "POST",
            "path": "/defense/evaluate",
            "tenant_id": "test-tenant",
            "timestamp_ms": 1234567890000,
            "request_id": "test-request-id",
            "body": {"test": "data"},
        }

        headers1 = signer.sign_request(**params)
        headers2 = signer.sign_request(**params)

        # Signatures should be identical
        assert headers1["X-GATE-SIGNATURE"] == headers2["X-GATE-SIGNATURE"]

        # All headers should be set
        assert headers1["X-GATE-TENANT-ID"] == "test-tenant"
        assert headers1["X-GATE-KEY-ID"] == "test-key"
        assert headers1["X-GATE-TIMESTAMP-MS"] == "1234567890000"
        assert headers1["X-GATE-REQUEST-ID"] == "test-request-id"
        assert len(headers1["X-GATE-SIGNATURE"]) == 64  # Hex signature

    def test_different_bodies_produce_different_signatures(self):
        """Test that different bodies produce different signatures"""
        signer = HmacSigner(key_id="test-key", secret="test-secret")

        base_params = {
            "method": "POST",
            "path": "/defense/evaluate",
            "tenant_id": "test-tenant",
            "timestamp_ms": 1234567890000,
            "request_id": "test-request-id",
        }

        headers1 = signer.sign_request(**base_params, body={"a": 1})
        headers2 = signer.sign_request(**base_params, body={"a": 2})

        # Signatures should differ
        assert headers1["X-GATE-SIGNATURE"] != headers2["X-GATE-SIGNATURE"]

    def test_golden_vector(self):
        """Test with golden vector (known input -> known output)"""
        signer = HmacSigner(
            key_id="key-001",
            secret="test-secret-key-do-not-use-in-production",
        )

        # Known input
        params = {
            "method": "POST",
            "path": "/defense/evaluate",
            "tenant_id": "tenant-123",
            "timestamp_ms": 1704067200000,  # 2024-01-01 00:00:00 UTC
            "request_id": "req-abc-123",
            "body": {
                "tx_intent": {
                    "from": "0x1234567890123456789012345678901234567890",
                    "to": "0x0987654321098765432109876543210987654321",
                    "value": "1000000000000000000",
                },
                "signing_context": {
                    "signerId": "test-signer",
                },
            },
        }

        headers = signer.sign_request(**params)

        # Verify signature format
        assert headers["X-GATE-SIGNATURE"]
        assert len(headers["X-GATE-SIGNATURE"]) == 64  # Hex signature

        # Verify signature can be verified
        # Reconstruct signing string (must match implementation in auth.py)
        body_json = canonical_json(params["body"])
        body_hash = sha256_hex(body_json)

        signing_string = "\n".join([
            "v1",
            "POST",
            "/defense/evaluate",
            "tenant-123",
            "key-001",  # key_id from signer
            "1704067200000",
            "req-abc-123",
            body_hash,
        ])

        # Compute expected signature
        expected_sig = hmac.new(
            b"test-secret-key-do-not-use-in-production",
            signing_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        assert headers["X-GATE-SIGNATURE"] == expected_sig

