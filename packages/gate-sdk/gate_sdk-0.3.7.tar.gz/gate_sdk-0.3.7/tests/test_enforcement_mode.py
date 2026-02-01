"""
Unit Tests for GateClient - Enforcement Mode

Tests hard enforcement mode, IAM permission risk checking, and override flags.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from gate_sdk.client import GateClient, GateClientConfig
from gate_sdk.auth import ApiKeyAuth
from gate_sdk.security import IamPermissionRiskChecker, IamPermissionRiskCheckerOptions


@pytest.fixture
def base_config():
    """Base configuration for tests"""
    return GateClientConfig(
        base_url='https://api.example.com',
        tenant_id='tenant-123',
        auth=ApiKeyAuth(mode='apiKey', api_key='test-api-key'),
        timeout_ms=50,
        local=True,  # Skip heartbeat for enforcement mode tests
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
        mock.return_value = manager
        manager.get_token.return_value = 'mock-heartbeat-token'
        manager.start = Mock()
        yield manager


class TestEnforcementModeSoft:
    """Tests for SOFT enforcement mode (default)"""

    def test_soft_mode_initializes_with_aws_credentials(self, base_config, mock_http_client, mock_heartbeat_manager):
        """SOFT mode should initialize even with AWS credentials present"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'

        base_config.enforcement_mode = 'SOFT'

        # Should not raise
        client = GateClient(base_config)
        assert client is not None

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']
        del os.environ['AWS_SECRET_ACCESS_KEY']

    def test_soft_mode_defaults_when_not_specified(self, base_config, mock_http_client, mock_heartbeat_manager):
        """Should default to SOFT mode when not specified"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'

        # No enforcement_mode specified
        client = GateClient(base_config)
        assert client is not None

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']

    def test_soft_mode_allows_override_flag(self, base_config, mock_http_client, mock_heartbeat_manager):
        """SOFT mode should allow override flag (though it doesn't block anyway)"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'

        base_config.enforcement_mode = 'SOFT'
        base_config.allow_insecure_kms_sign_permission = False

        # Should not raise
        client = GateClient(base_config)
        assert client is not None

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']


class TestEnforcementModeHard:
    """Tests for HARD enforcement mode"""

    def test_hard_mode_blocks_with_risk_and_no_override(self, base_config, mock_http_client, mock_heartbeat_manager):
        """HARD mode should block initialization when risk detected and override not set"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['GATE_HEARTBEAT_KEY'] = 'test-heartbeat-key'  # Required for non-local mode

        base_config.enforcement_mode = 'HARD'
        base_config.allow_insecure_kms_sign_permission = False
        base_config.local = False  # Need non-local mode to test enforcement

        # Mock risk checker to detect risk
        with patch('gate_sdk.client.IamPermissionRiskChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.check_sync.side_effect = RuntimeError(
                '[GATE ERROR] Hard enforcement mode blocked initialization'
            )
            mock_checker_class.return_value = mock_checker

            with pytest.raises(RuntimeError, match='Hard enforcement mode blocked initialization'):
                GateClient(base_config)

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']
        if 'GATE_HEARTBEAT_KEY' in os.environ:
            del os.environ['GATE_HEARTBEAT_KEY']

    def test_hard_mode_allows_with_override(self, base_config, mock_http_client, mock_heartbeat_manager):
        """HARD mode should allow initialization when override is set"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['GATE_HEARTBEAT_KEY'] = 'test-heartbeat-key'  # Required for non-local mode

        base_config.enforcement_mode = 'HARD'
        base_config.allow_insecure_kms_sign_permission = True
        base_config.local = False  # Need non-local mode to test enforcement

        # Mock risk checker to detect risk but allow with override
        with patch('gate_sdk.client.IamPermissionRiskChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.check_sync.return_value = Mock(has_risk=True, confidence='MEDIUM')
            mock_checker_class.return_value = mock_checker

            # Should not raise
            client = GateClient(base_config)
            assert client is not None

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']
        if 'GATE_HEARTBEAT_KEY' in os.environ:
            del os.environ['GATE_HEARTBEAT_KEY']

    def test_hard_mode_allows_with_no_risk(self, base_config, mock_http_client, mock_heartbeat_manager):
        """HARD mode should allow initialization when no risk detected"""
        # No AWS credentials
        os.environ['GATE_HEARTBEAT_KEY'] = 'test-heartbeat-key'  # Required for non-local mode

        base_config.enforcement_mode = 'HARD'
        base_config.allow_insecure_kms_sign_permission = False
        base_config.local = False  # Need non-local mode to test enforcement

        # Mock risk checker to return no risk
        with patch('gate_sdk.client.IamPermissionRiskChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.check_sync.return_value = Mock(has_risk=False, confidence='LOW')
            mock_checker_class.return_value = mock_checker

            # Should not raise
            client = GateClient(base_config)
            assert client is not None

        # Cleanup
        if 'GATE_HEARTBEAT_KEY' in os.environ:
            del os.environ['GATE_HEARTBEAT_KEY']

    def test_hard_mode_defaults_override_to_false(self, base_config, mock_http_client, mock_heartbeat_manager):
        """HARD mode should default allow_insecure_kms_sign_permission to False"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['GATE_HEARTBEAT_KEY'] = 'test-heartbeat-key'  # Required for non-local mode

        base_config.enforcement_mode = 'HARD'
        base_config.local = False  # Need non-local mode to test enforcement
        # allow_insecure_kms_sign_permission not set

        # Mock risk checker to detect risk
        with patch('gate_sdk.client.IamPermissionRiskChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.check_sync.side_effect = RuntimeError(
                '[GATE ERROR] Hard enforcement mode blocked initialization'
            )
            mock_checker_class.return_value = mock_checker

            with pytest.raises(RuntimeError):
                GateClient(base_config)

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']
        if 'GATE_HEARTBEAT_KEY' in os.environ:
            del os.environ['GATE_HEARTBEAT_KEY']


class TestLocalMode:
    """Tests for local mode (skips IAM risk check)"""

    def test_local_mode_skips_iam_check(self, base_config, mock_http_client):
        """Local mode should skip IAM risk check"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'

        base_config.local = True
        base_config.enforcement_mode = 'HARD'
        base_config.allow_insecure_kms_sign_permission = False

        # Should not raise even with HARD mode and risk
        client = GateClient(base_config)
        assert client is not None

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']


class TestIamPermissionRiskChecker:
    """Tests for IamPermissionRiskChecker"""

    def test_check_sync_no_risk(self):
        """Should return no risk when no AWS credentials detected"""
        # Ensure no AWS credentials are present
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 
                    'AWS_ROLE_ARN', 'AWS_WEB_IDENTITY_TOKEN_FILE', 'KMS_KEY_ID']
        saved_vars = {}
        for var in aws_vars:
            if var in os.environ:
                saved_vars[var] = os.environ[var]
                del os.environ[var]
        
        try:
            options = IamPermissionRiskCheckerOptions(
                tenant_id='tenant-123',
                enforcement_mode='SOFT',
                allow_insecure_kms_sign_permission=True,
            )

            checker = IamPermissionRiskChecker(options)
            result = checker.check_sync()

            assert result.has_risk is False
            assert result.confidence == 'LOW'
        finally:
            # Restore environment variables
            for var, value in saved_vars.items():
                os.environ[var] = value

    def test_check_sync_detects_aws_credentials(self):
        """Should detect risk when AWS credentials are present"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'

        options = IamPermissionRiskCheckerOptions(
            tenant_id='tenant-123',
            enforcement_mode='SOFT',
            allow_insecure_kms_sign_permission=True,
        )

        checker = IamPermissionRiskChecker(options)
        result = checker.check_sync()

        assert result.has_risk is True
        assert result.risk_type == 'AWS_CREDENTIALS_DETECTED'
        assert result.confidence == 'MEDIUM'
        assert 'Remove kms:Sign permission' in result.remediation

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']
        del os.environ['AWS_SECRET_ACCESS_KEY']

    def test_check_sync_hard_mode_raises(self):
        """Should raise error in HARD mode when risk detected and override not set"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'

        options = IamPermissionRiskCheckerOptions(
            tenant_id='tenant-123',
            enforcement_mode='HARD',
            allow_insecure_kms_sign_permission=False,
        )

        checker = IamPermissionRiskChecker(options)

        with pytest.raises(RuntimeError, match='Hard enforcement mode blocked initialization'):
            checker.check_sync()

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']

    def test_check_sync_hard_mode_with_override(self):
        """Should not raise in HARD mode when override is set"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'

        options = IamPermissionRiskCheckerOptions(
            tenant_id='tenant-123',
            enforcement_mode='HARD',
            allow_insecure_kms_sign_permission=True,
        )

        checker = IamPermissionRiskChecker(options)
        result = checker.check_sync()

        # Should log warning but not raise
        assert result.has_risk is True

        # Cleanup
        del os.environ['AWS_ACCESS_KEY_ID']

    def test_check_sync_detects_environment_markers(self):
        """Should detect environment markers"""
        os.environ['KMS_KEY_ID'] = 'test-key-id'

        options = IamPermissionRiskCheckerOptions(
            tenant_id='tenant-123',
            enforcement_mode='SOFT',
            allow_insecure_kms_sign_permission=True,
        )

        checker = IamPermissionRiskChecker(options)
        result = checker.check_sync()

        assert result.has_risk is True
        assert result.risk_type == 'ENVIRONMENT_MARKERS'
        assert result.confidence == 'LOW'

        # Cleanup
        del os.environ['KMS_KEY_ID']

    def test_check_sync_detects_role_credentials(self):
        """Should detect role credentials"""
        os.environ['AWS_ROLE_ARN'] = 'arn:aws:iam::123456789012:role/TestRole'

        options = IamPermissionRiskCheckerOptions(
            tenant_id='tenant-123',
            enforcement_mode='SOFT',
            allow_insecure_kms_sign_permission=True,
        )

        checker = IamPermissionRiskChecker(options)
        result = checker.check_sync()

        assert result.has_risk is True
        assert result.risk_type == 'AWS_CREDENTIALS_DETECTED'

        # Cleanup
        del os.environ['AWS_ROLE_ARN']



