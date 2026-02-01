"""
Tests for Gate KMS wrapper
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from gate_sdk import GateClient, GateClientConfig, HmacAuth, BlockIntelBlockedError, BlockIntelStepUpRequiredError
from gate_sdk.kms import wrap_kms_client, WrappedKmsClient, WrapKmsClientOptions


@pytest.fixture
def mock_gate_client():
    """Create a mock Gate client"""
    config = GateClientConfig(
        base_url="https://gate.example.com",
        tenant_id="test-tenant",
        auth=HmacAuth(mode="hmac", key_id="test-key", secret="test-secret"),
        local=True,  # Use local mode to skip heartbeat initialization in tests
    )
    gate_client = GateClient(config)
    gate_client.evaluate = Mock()
    # Mock heartbeat manager if it exists (local mode may not have one)
    if gate_client._heartbeat_manager:
        gate_client._heartbeat_manager.get_token = Mock(return_value="mock-heartbeat-token")
    return gate_client


@pytest.fixture
def mock_kms_client():
    """Create a mock boto3 KMS client"""
    kms = Mock()
    kms.sign = Mock(return_value={"Signature": b"mock-signature", "KeyId": "alias/test-key"})
    return kms


class TestWrapKmsClient:
    """Test KMS wrapper functionality"""

    def test_wrap_kms_client_allows_when_gate_allows(self, mock_gate_client, mock_kms_client):
        """Test that wrapped client forwards to KMS when Gate allows"""
        # Mock Gate evaluate() to allow
        mock_gate_client.evaluate.return_value = {"decision": "ALLOW", "reasonCodes": []}

        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client)

        # Call sign()
        result = wrapped.sign(
            KeyId="alias/test-key",
            Message=b"test message",
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )

        # Verify Gate was called
        assert mock_gate_client.evaluate.called
        call_args = mock_gate_client.evaluate.call_args[0][0]
        # signerId is normalized (alias/ prefix removed) to match heartbeat format
        assert call_args["signingContext"]["signerId"] == "test-key"
        assert call_args["txIntent"]["networkFamily"] == "OTHER"

        # Verify KMS was called
        assert mock_kms_client.sign.called

        # Verify result
        assert result["Signature"] == b"mock-signature"

    def test_wrap_kms_client_blocks_when_gate_blocks(self, mock_gate_client, mock_kms_client):
        """Test that wrapped client blocks and does NOT call KMS when Gate blocks"""
        # Mock Gate evaluate() to throw BLOCK error
        blocked_error = BlockIntelBlockedError("TO_ADDRESS_DENYLISTED", "receipt-123")
        mock_gate_client.evaluate.side_effect = blocked_error

        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client)

        # Call sign() - should raise BlockIntelBlockedError
        with pytest.raises(BlockIntelBlockedError, match="TO_ADDRESS_DENYLISTED"):
            wrapped.sign(
                KeyId="alias/test-key",
                Message=b"test message",
                MessageType="RAW",
                SigningAlgorithm="ECDSA_SHA_256",
            )

        # Verify Gate was called
        assert mock_gate_client.evaluate.called

        # Verify KMS was NOT called
        assert not mock_kms_client.sign.called

    def test_wrap_kms_client_requires_stepup_when_gate_requires(self, mock_gate_client, mock_kms_client):
        """Test that wrapped client raises StepUpRequiredError when Gate requires step-up"""
        step_up_error = BlockIntelStepUpRequiredError("stepup-123", "/defense/stepup/status")
        mock_gate_client.evaluate.side_effect = step_up_error

        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client)

        # Call sign() - should raise BlockIntelStepUpRequiredError
        with pytest.raises(BlockIntelStepUpRequiredError):
            wrapped.sign(
                KeyId="alias/test-key",
                Message=b"test message",
                MessageType="RAW",
                SigningAlgorithm="ECDSA_SHA_256",
            )

        # Verify Gate was called
        assert mock_gate_client.evaluate.called

        # Verify KMS was NOT called
        assert not mock_kms_client.sign.called

    def test_wrap_kms_client_invokes_on_decision_callback(self, mock_gate_client, mock_kms_client):
        """Test that on_decision callback is invoked"""
        on_decision = Mock()

        mock_gate_client.evaluate.return_value = {"decision": "ALLOW", "reasonCodes": []}

        options = WrapKmsClientOptions(on_decision=on_decision)
        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client, options)

        wrapped.sign(
            KeyId="alias/test-key",
            Message=b"test message",
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )

        # Verify callback was called
        assert on_decision.called
        call_args = on_decision.call_args[0]
        assert call_args[0] == "ALLOW"

    def test_wrap_kms_client_uses_custom_extract_tx_intent(self, mock_gate_client, mock_kms_client):
        """Test that custom extract_tx_intent hook is used if provided"""
        custom_extract = Mock(return_value={
            "networkFamily": "EVM",
            "toAddress": "0x1234567890123456789012345678901234567890",
            "chainId": 1,
            "payloadHash": "custom-hash",
        })

        mock_gate_client.evaluate.return_value = {"decision": "ALLOW", "reasonCodes": []}

        options = WrapKmsClientOptions(extract_tx_intent=custom_extract)
        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client, options)

        wrapped.sign(
            KeyId="alias/test-key",
            Message=b"test message",
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )

        # Verify custom hook was called
        assert custom_extract.called

        # Verify Gate was called with custom txIntent
        call_args = mock_gate_client.evaluate.call_args[0][0]
        assert call_args["txIntent"]["networkFamily"] == "EVM"
        assert call_args["txIntent"]["toAddress"] == "0x1234567890123456789012345678901234567890"
        assert call_args["txIntent"]["chainId"] == 1

    def test_wrap_kms_client_dry_run_mode(self, mock_gate_client, mock_kms_client):
        """Test that dry-run mode evaluates but still allows KMS call"""
        mock_gate_client.evaluate.return_value = {"decision": "ALLOW", "reasonCodes": []}

        options = WrapKmsClientOptions(mode="dry-run")
        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client, options)

        result = wrapped.sign(
            KeyId="alias/test-key",
            Message=b"test message",
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )

        # Verify Gate was called
        assert mock_gate_client.evaluate.called

        # In dry-run mode, KMS is still called
        assert mock_kms_client.sign.called

        # Verify result
        assert result["Signature"] == b"mock-signature"

    def test_default_extract_tx_intent_computes_message_hash(self):
        """Test that default extract_tx_intent computes SHA256 hash of message"""
        from gate_sdk.kms import default_extract_tx_intent

        sign_params = {
            "KeyId": "alias/test-key",
            "Message": b"test message",
            "MessageType": "RAW",
            "SigningAlgorithm": "ECDSA_SHA_256",
        }

        tx_intent = default_extract_tx_intent(sign_params)

        assert tx_intent["networkFamily"] == "OTHER"
        assert tx_intent["payloadHash"] is not None
        assert tx_intent["dataHash"] == tx_intent["payloadHash"]
        assert len(tx_intent["payloadHash"]) == 64  # SHA256 hex length


class TestWrappedKmsClient:
    """Test WrappedKmsClient class"""

    def test_wrapped_client_preserves_original_attributes(self, mock_gate_client, mock_kms_client):
        """Test that wrapped client preserves original client attributes"""
        # Add a custom attribute to original client
        mock_kms_client.custom_attr = "test-value"

        wrapped = wrap_kms_client(mock_kms_client, mock_gate_client)

        # Wrapped client should expose metadata
        assert hasattr(wrapped, "_original_client")
        assert hasattr(wrapped, "_gate_client")
        assert hasattr(wrapped, "_options")

