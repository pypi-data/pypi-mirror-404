"""
BlockIntel Gate SDK - IAM Permission Risk Checker

Best-effort detection of IAM permissions that could bypass Gate.
"""

import os
import logging
from typing import Optional, List, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EnforcementMode = Literal['SOFT', 'HARD']


@dataclass
class IamPermissionRiskCheckResult:
    """Result of IAM permission risk check"""

    has_risk: bool
    risk_type: Optional[Literal['DIRECT_KMS_SIGN_PERMISSION', 'AWS_CREDENTIALS_DETECTED', 'ENVIRONMENT_MARKERS']] = None
    confidence: Literal['HIGH', 'MEDIUM', 'LOW'] = 'LOW'
    details: str = ''
    remediation: Optional[str] = None


@dataclass
class IamPermissionRiskCheckerOptions:
    """Options for IAM permission risk checker"""

    tenant_id: str
    signer_id: Optional[str] = None
    environment: Optional[str] = None
    enforcement_mode: EnforcementMode = 'SOFT'
    allow_insecure_kms_sign_permission: bool = False
    kms_key_ids: Optional[List[str]] = None


class IamPermissionRiskChecker:
    """
    IAM Permission Risk Checker

    Performs best-effort detection of IAM permissions that could allow
    direct KMS signing, bypassing Gate SDK.
    """

    def __init__(self, options: IamPermissionRiskCheckerOptions):
        self.options = options

    def check_sync(self) -> IamPermissionRiskCheckResult:
        """
        Perform synchronous IAM permission risk check

        Performs quick checks (credentials, environment markers) synchronously.
        In HARD mode, raises error if risk detected and override not set.

        Returns:
            Risk assessment result

        Raises:
            RuntimeError: In HARD mode if risk detected and override not set
        """
        checks: List[IamPermissionRiskCheckResult] = []

        # Check 1: AWS Credentials Presence
        credentials_check = self._check_aws_credentials()
        if credentials_check.has_risk:
            checks.append(credentials_check)

        # Check 2: Environment Markers
        env_check = self._check_environment_markers()
        if env_check.has_risk:
            checks.append(env_check)

        # Aggregate results
        if not checks:
            return IamPermissionRiskCheckResult(
                has_risk=False,
                confidence='LOW',
                details='No IAM permission risk detected (synchronous check)',
            )

        highest_confidence = self._get_highest_confidence(checks)
        highest_risk = next((c for c in checks if c.confidence == highest_confidence), None)

        if not highest_risk or not highest_risk.has_risk:
            return IamPermissionRiskCheckResult(
                has_risk=False,
                confidence='LOW',
                details='No IAM permission risk detected (synchronous check)',
            )

        # In HARD mode, raise error if risk detected and override not set
        if self.options.enforcement_mode == 'HARD' and not self.options.allow_insecure_kms_sign_permission:
            error_message = self._build_error_message(highest_risk)
            raise RuntimeError(error_message)

        # Log warning in SOFT mode or if override is set
        self._log_warning(highest_risk)

        return highest_risk

    async def check(self) -> IamPermissionRiskCheckResult:
        """
        Perform full IAM permission risk check (including async IAM simulation)

        Returns:
            Risk assessment result

        Raises:
            RuntimeError: In HARD mode if risk detected and override not set
        """
        # First do synchronous checks
        sync_result = self.check_sync()

        # If sync check found risk and we're in HARD mode, it already raised
        # If we're here, either no risk or SOFT mode - continue with async checks

        # Check 3: IAM Permission Simulation (if available) - async
        simulation_check = await self._check_iam_simulation()
        if simulation_check.has_risk:
            # In HARD mode, raise error if risk detected and override not set
            if self.options.enforcement_mode == 'HARD' and not self.options.allow_insecure_kms_sign_permission:
                error_message = self._build_error_message(simulation_check)
                raise RuntimeError(error_message)

            # Log warning in SOFT mode or if override is set
            self._log_warning(simulation_check)

            return simulation_check

        # Return sync result (no async risk found)
        return sync_result

    def _check_aws_credentials(self) -> IamPermissionRiskCheckResult:
        """Check if AWS credentials are present"""
        has_env_vars = bool(
            os.getenv('AWS_ACCESS_KEY_ID') or
            os.getenv('AWS_SECRET_ACCESS_KEY') or
            os.getenv('AWS_SESSION_TOKEN')
        )

        has_role_credentials = bool(
            os.getenv('AWS_ROLE_ARN') or
            os.getenv('AWS_WEB_IDENTITY_TOKEN_FILE') or
            os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')
        )

        if has_env_vars or has_role_credentials:
            return IamPermissionRiskCheckResult(
                has_risk=True,
                risk_type='AWS_CREDENTIALS_DETECTED',
                confidence='MEDIUM',
                details='AWS credentials detected in environment. Application may have direct KMS signing permissions.',
                remediation='Remove kms:Sign permission from application role. See https://docs.blockintelai.com/gate/IAM_HARDENING',
            )

        return IamPermissionRiskCheckResult(
            has_risk=False,
            confidence='LOW',
            details='No AWS credentials detected in environment variables',
        )

    async def _check_iam_simulation(self) -> IamPermissionRiskCheckResult:
        """Check IAM permissions using simulation API (if available)"""
        try:
            # Try to use boto3 if available
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                # boto3 not available - skip simulation
                return IamPermissionRiskCheckResult(
                    has_risk=False,
                    confidence='LOW',
                    details='boto3 not available for IAM simulation',
                )

            # Get current principal ARN (best-effort)
            principal_arn = await self._get_current_principal_arn()
            if not principal_arn:
                return IamPermissionRiskCheckResult(
                    has_risk=False,
                    confidence='LOW',
                    details='Could not determine current principal ARN for simulation',
                )

            # Try to simulate kms:Sign permission
            iam_client = boto3.client('iam')
            resource_arns = (
                [f'arn:aws:kms:*:*:key/{key_id}' for key_id in self.options.kms_key_ids]
                if self.options.kms_key_ids
                else ['arn:aws:kms:*:*:key/*']
            )

            try:
                response = iam_client.simulate_principal_policy(
                    PolicySourceArn=principal_arn,
                    ActionNames=['kms:Sign'],
                    ResourceArns=resource_arns,
                )

                # Check if any evaluation result allows kms:Sign
                allows_sign = any(
                    result.get('EvalDecision') in ('allowed', 'explicitAllow')
                    for result in response.get('EvaluationResults', [])
                )

                if allows_sign:
                    return IamPermissionRiskCheckResult(
                        has_risk=True,
                        risk_type='DIRECT_KMS_SIGN_PERMISSION',
                        confidence='HIGH',
                        details=f'IAM simulation confirms principal {principal_arn} has kms:Sign permission. Direct KMS signing can bypass Gate.',
                        remediation='Remove kms:Sign permission from application role. See https://docs.blockintelai.com/gate/IAM_HARDENING',
                    )

                return IamPermissionRiskCheckResult(
                    has_risk=False,
                    confidence='HIGH',
                    details='IAM simulation confirms no kms:Sign permission',
                )
            except ClientError as e:
                # Simulation failed (likely due to missing permissions)
                return IamPermissionRiskCheckResult(
                    has_risk=False,
                    confidence='LOW',
                    details=f'IAM simulation not available: {str(e)}',
                )
        except Exception as e:
            # Simulation failed - fall back to other checks
            return IamPermissionRiskCheckResult(
                has_risk=False,
                confidence='LOW',
                details=f'IAM simulation failed: {str(e)}',
            )

    def _check_environment_markers(self) -> IamPermissionRiskCheckResult:
        """Check environment markers that suggest direct KMS usage"""
        markers = [
            'KMS_KEY_ID',
            'AWS_KMS_KEY_ID',
            'KMS_KEY_ARN',
            'AWS_KMS_KEY_ARN',
        ]

        found_markers = [marker for marker in markers if os.getenv(marker)]

        if found_markers:
            return IamPermissionRiskCheckResult(
                has_risk=True,
                risk_type='ENVIRONMENT_MARKERS',
                confidence='LOW',
                details=f'Environment markers suggest direct KMS usage: {", ".join(found_markers)}',
                remediation='Review environment variables and ensure KMS access is gated through Gate SDK',
            )

        return IamPermissionRiskCheckResult(
            has_risk=False,
            confidence='LOW',
            details='No environment markers suggesting direct KMS usage',
        )

    async def _get_current_principal_arn(self) -> Optional[str]:
        """Get current principal ARN (best-effort)"""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return None

        try:
            # Try to get from STS GetCallerIdentity
            sts_client = boto3.client('sts')
            response = sts_client.get_caller_identity()
            return response.get('Arn')
        except (ClientError, Exception):
            # Ignore errors - best-effort only
            return None

    def _get_highest_confidence(self, checks: List[IamPermissionRiskCheckResult]) -> Literal['HIGH', 'MEDIUM', 'LOW']:
        """Get highest confidence level from checks"""
        if any(c.confidence == 'HIGH' for c in checks):
            return 'HIGH'
        if any(c.confidence == 'MEDIUM' for c in checks):
            return 'MEDIUM'
        return 'LOW'

    def _build_error_message(self, result: IamPermissionRiskCheckResult) -> str:
        """Build error message for HARD mode"""
        parts = [
            '[GATE ERROR] Hard enforcement mode blocked initialization:',
            f'  - IAM permission risk: {result.details}',
            f'  - Risk type: {result.risk_type}',
            f'  - Confidence: {result.confidence}',
            f'  - Tenant ID: {self.options.tenant_id}',
        ]

        if self.options.signer_id:
            parts.append(f'  - Signer ID: {self.options.signer_id}')

        if self.options.environment:
            parts.append(f'  - Environment: {self.options.environment}')

        if result.remediation:
            parts.append(f'  - Remediation: {result.remediation}')

        parts.append('  - See: https://docs.blockintelai.com/gate/IAM_HARDENING')
        parts.append('  - Override: Set allow_insecure_kms_sign_permission=True (not recommended for production)')

        return '\n'.join(parts)

    def _log_warning(self, result: IamPermissionRiskCheckResult) -> None:
        """Log warning (SOFT mode or override set)"""
        log_data = {
            'level': 'WARN',
            'message': 'IAM permission risk detected',
            'tenant_id': self.options.tenant_id,
            'signer_id': self.options.signer_id,
            'environment': self.options.environment,
            'enforcement_mode': self.options.enforcement_mode,
            'risk_type': result.risk_type,
            'confidence': result.confidence,
            'details': result.details,
            'remediation': result.remediation,
            'documentation': 'https://docs.blockintelai.com/gate/IAM_HARDENING',
        }

        logger.warning('[GATE WARNING] %s', log_data)

