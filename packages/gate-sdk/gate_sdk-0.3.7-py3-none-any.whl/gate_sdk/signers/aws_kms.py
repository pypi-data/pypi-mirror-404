"""
AWS KMS Signer Backend

Implements SignerBackend for AWS KMS using boto3
"""

import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from .base import SignerBackend, SignRequest, SignResponse


class AwsKmsSignerConfig:
    """AWS KMS signer configuration"""
    
    def __init__(
        self,
        kms_client=None,  # boto3.client('kms')
        default_algorithm: str = 'ECDSA_SHA_256',
        default_message_type: str = 'RAW',
        region_name: Optional[str] = None,
    ):
        """
        Initialize AWS KMS signer config.
        
        Args:
            kms_client: boto3 KMS client instance (if None, creates new client)
            default_algorithm: Default signing algorithm
            default_message_type: Default message type (RAW or DIGEST)
            region_name: AWS region (if creating new client)
        """
        self.kms_client = kms_client or boto3.client('kms', region_name=region_name)
        self.default_algorithm = default_algorithm
        self.default_message_type = default_message_type


class AwsKmsSigner(SignerBackend):
    """AWS KMS Signer Backend"""
    
    def __init__(self, config: AwsKmsSignerConfig):
        """Initialize AWS KMS signer"""
        self.config = config
    
    def get_name(self) -> str:
        """Get backend name"""
        return 'AWS KMS'
    
    def is_available(self) -> bool:
        """Check if backend is available"""
        return self.config.kms_client is not None
    
    def sign(self, request: SignRequest) -> SignResponse:
        """Sign a message using AWS KMS"""
        if not self.is_available():
            raise ValueError('AWS KMS client not configured')
        
        algorithm = request.algorithm or self.config.default_algorithm
        message_type = request.message_type or self.config.default_message_type
        
        try:
            response = self.config.kms_client.sign(
                KeyId=request.key_id,
                Message=request.message,
                MessageType=message_type,
                SigningAlgorithm=algorithm,
            )
            
            if 'Signature' not in response:
                raise RuntimeError('AWS KMS sign response missing signature')
            
            return SignResponse(
                signature=response['Signature'],
                key_id=response.get('KeyId', request.key_id),
                algorithm=response.get('SigningAlgorithm', algorithm),
                metadata={
                    'key_id': response.get('KeyId'),
                    'signing_algorithm': response.get('SigningAlgorithm'),
                },
            )
        except ClientError as e:
            raise RuntimeError(f'AWS KMS sign failed: {e}') from e

