"""
Unit Tests for GateClient - Customer Adaptive Features

Tests shadow mode, fail strategy, and break-glass token support.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from gate_sdk.client import GateClient, GateClientConfig
from gate_sdk.types import GateMode, ConnectionFailureStrategy
from gate_sdk.auth import ApiKeyAuth
from gate_sdk.errors import (
    BlockIntelBlockedError,
    BlockIntelUnavailableError,
    GateError,
    GateTimeoutError,
    GateServerError,
)


@pytest.fixture
def base_config():
    """Base configuration for tests"""
    return GateClientConfig(
        base_url='https://api.example.com',
        tenant_id='tenant-123',
        auth=ApiKeyAuth(mode='apiKey', api_key='test-api-key'),
        timeout_ms=50,
        local=True,  # Use local mode to skip heartbeat initialization in tests
    )


@pytest.fixture
def mock_http_client():
    """Mock HTTP client"""
    with patch('gate_sdk.client.HttpClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_heartbeat_manager():
    """Mock heartbeat manager"""
    with patch('gate_sdk.client.HeartbeatManager') as mock:
        manager = Mock()
        manager.return_value = manager
        manager.get_token.return_value = 'mock-heartbeat-token'
        manager.start = Mock()
        yield manager


class TestShadowMode:
    """Tests for Shadow Mode"""

    def test_defaults_to_shadow_mode(self, base_config, mock_http_client, mock_heartbeat_manager):
        """Test that client defaults to SHADOW mode"""
        client = GateClient(base_config)
        assert client._mode == 'SHADOW'

    def test_uses_gate_mode_env_var(self, base_config, mock_http_client, mock_heartbeat_manager):
        """Test that GATE_MODE environment variable is used"""
        os.environ['GATE_MODE'] = 'ENFORCE'
        try:
            client = GateClient(base_config)
            assert client._mode == 'ENFORCE'
        finally:
            os.environ.pop('GATE_MODE', None)

    def test_uses_config_mode(self, base_config, mock_http_client, mock_heartbeat_manager):
        """Test that config.mode is used"""
        base_config.mode = 'ENFORCE'
        client = GateClient(base_config)
        assert client._mode == 'ENFORCE'

    def test_allows_transaction_in_shadow_mode_when_policy_blocks(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that transactions are allowed in SHADOW mode even when policy would block"""
        base_config.mode = 'SHADOW'
        client = GateClient(base_config)

        # Mock response with BLOCK decision
        mock_http_client.request.return_value = {
            'decision': 'BLOCK',
            'reason_codes': ['POLICY_VIOLATION'],
            'correlation_id': 'test-correlation-id',
        }

        result = client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        assert result['decision'] == 'ALLOW'
        assert result['shadowWouldBlock'] is True
        assert result['enforced'] is False
        assert result['mode'] == 'SHADOW'

    def test_blocks_transaction_in_enforce_mode_when_policy_blocks(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that transactions are blocked in ENFORCE mode when policy blocks"""
        base_config.mode = 'ENFORCE'
        client = GateClient(base_config)

        # Mock response with BLOCK decision
        mock_http_client.request.return_value = {
            'decision': 'BLOCK',
            'reason_codes': ['POLICY_VIOLATION'],
            'correlation_id': 'test-correlation-id',
        }

        with pytest.raises(BlockIntelBlockedError):
            client.evaluate({
                'txIntent': {
                    'from': '0x123',
                    'to': '0x456',
                    'value': '1.0',
                },
            })

    def test_includes_mode_in_request_body(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that mode is included in request body"""
        base_config.mode = 'SHADOW'
        client = GateClient(base_config)

        mock_http_client.request.return_value = {
            'decision': 'ALLOW',
            'reason_codes': [],
            'correlation_id': 'test-correlation-id',
        }

        client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        # Check that mode was included in request
        call_args = mock_http_client.request.call_args
        assert call_args is not None
        body = call_args[1]['body']
        assert body['mode'] == 'SHADOW'


class TestFailStrategy:
    """Tests for Fail Strategy"""

    def test_defaults_to_fail_open_in_shadow_mode(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that FAIL_OPEN is default in SHADOW mode"""
        base_config.mode = 'SHADOW'
        client = GateClient(base_config)
        assert client._on_connection_failure == 'FAIL_OPEN'

    def test_defaults_to_fail_closed_in_enforce_mode(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that FAIL_CLOSED is default in ENFORCE mode"""
        base_config.mode = 'ENFORCE'
        client = GateClient(base_config)
        assert client._on_connection_failure == 'FAIL_CLOSED'

    def test_uses_config_on_connection_failure(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that config.on_connection_failure is used"""
        base_config.mode = 'ENFORCE'
        base_config.on_connection_failure = 'FAIL_OPEN'
        client = GateClient(base_config)
        assert client._on_connection_failure == 'FAIL_OPEN'

    def test_allows_transaction_on_connection_failure_with_fail_open(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that transactions are allowed on connection failure with FAIL_OPEN"""
        base_config.mode = 'SHADOW'
        base_config.on_connection_failure = 'FAIL_OPEN'
        client = GateClient(base_config)

        # Mock connection failure (timeout)
        mock_http_client.request.side_effect = GateTimeoutError('Request timeout')

        result = client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        assert result['decision'] == 'ALLOW'
        assert 'GATE_HOTPATH_UNAVAILABLE' in result['reasonCodes']
        assert result['enforced'] is False

    def test_blocks_transaction_on_connection_failure_with_fail_closed(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that transactions are blocked on connection failure with FAIL_CLOSED"""
        base_config.mode = 'ENFORCE'
        base_config.on_connection_failure = 'FAIL_CLOSED'
        client = GateClient(base_config)

        # Mock connection failure (timeout)
        mock_http_client.request.side_effect = GateTimeoutError('Request timeout')

        with pytest.raises(BlockIntelUnavailableError):
            client.evaluate({
                'txIntent': {
                    'from': '0x123',
                    'to': '0x456',
                    'value': '1.0',
                },
            })

    def test_handles_5xx_server_errors_with_fail_open(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that 5xx server errors are handled with FAIL_OPEN"""
        base_config.mode = 'SHADOW'
        base_config.on_connection_failure = 'FAIL_OPEN'
        client = GateClient(base_config)

        # Mock 5xx server error
        mock_http_client.request.side_effect = GateServerError('Internal server error')

        result = client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        assert result['decision'] == 'ALLOW'
        assert 'GATE_HOTPATH_UNAVAILABLE' in result['reasonCodes']


class TestBreakglassToken:
    """Tests for Break-glass Token"""

    def test_includes_breakglass_token_in_signing_context_if_configured(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that breakglassToken is included in signingContext if configured"""
        base_config.breakglass_token = 'test-breakglass-token'
        base_config.local = False  # Breakglass tokens are skipped in local mode
        # Mock GATE_HEARTBEAT_KEY environment variable for heartbeat initialization
        with patch.dict(os.environ, {'GATE_HEARTBEAT_KEY': 'test-heartbeat-key'}):
            client = GateClient(base_config)

            mock_http_client.request.return_value = {
                'decision': 'ALLOW',
                'reason_codes': [],
                'correlation_id': 'test-correlation-id',
            }

            client.evaluate({
                'txIntent': {
                    'from': '0x123',
                    'to': '0x456',
                    'value': '1.0',
                },
            })

            # Check that breakglassToken was included in request
            call_args = mock_http_client.request.call_args
            assert call_args is not None
            body = call_args[1]['body']
            assert body['signingContext']['breakglassToken'] == 'test-breakglass-token'

    def test_does_not_include_breakglass_token_if_not_configured(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that breakglassToken is not included if not configured"""
        client = GateClient(base_config)

        mock_http_client.request.return_value = {
            'decision': 'ALLOW',
            'reason_codes': [],
            'correlation_id': 'test-correlation-id',
        }

        client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        # Check that breakglassToken was not included in request
        call_args = mock_http_client.request.call_args
        assert call_args is not None
        body = call_args[1]['body']
        assert 'breakglassToken' not in body['signingContext']


class TestMetrics:
    """Tests for Metrics"""

    def test_records_would_block_metric_in_shadow_mode(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that WOULD_BLOCK metric is recorded in shadow mode"""
        base_config.mode = 'SHADOW'
        client = GateClient(base_config)

        # Mock response with BLOCK decision
        mock_http_client.request.return_value = {
            'decision': 'BLOCK',
            'reason_codes': ['POLICY_VIOLATION'],
            'correlation_id': 'test-correlation-id',
        }

        client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        metrics = client.get_metrics()
        assert metrics.would_block_total > 0

    def test_records_fail_open_metric_on_connection_failure(
        self, base_config, mock_http_client, mock_heartbeat_manager
    ):
        """Test that FAIL_OPEN metric is recorded on connection failure"""
        base_config.mode = 'SHADOW'
        base_config.on_connection_failure = 'FAIL_OPEN'
        client = GateClient(base_config)

        # Mock connection failure (timeout)
        mock_http_client.request.side_effect = GateTimeoutError('Request timeout')

        client.evaluate({
            'txIntent': {
                'from': '0x123',
                'to': '0x456',
                'value': '1.0',
            },
        })

        metrics = client.get_metrics()
        assert metrics.fail_open_total > 0

