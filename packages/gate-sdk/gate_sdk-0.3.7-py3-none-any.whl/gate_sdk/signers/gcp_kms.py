"""
Google Cloud KMS Signer Backend

Implements SignerBackend for Google Cloud KMS
"""

import os
import base64
import json
import requests
from typing import Optional, Dict, Any, Union

from .base import SignerBackend, SignRequest, SignResponse


class GcpKmsSignerConfig:
    """GCP KMS signer configuration"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,  # From GCP_PROJECT env var if not provided
        location: Optional[str] = None,  # From GCP_LOCATION env var if not provided
        key_ring: Optional[str] = None,  # From GCP_KEYRING env var if not provided
        credentials: Optional[Union[str, Dict[str, str]]] = None,  # Service account JSON or path
        use_workload_identity: bool = False,  # Use GCP metadata service
        default_algorithm: str = 'EC_SIGN_P256_SHA256',
        timeout: int = 5,
    ):
        """
        Initialize GCP KMS signer config.
        
        Args:
            project_id: GCP project ID (default: GCP_PROJECT env var)
            location: GCP location (default: GCP_LOCATION env var)
            key_ring: Key ring name (default: GCP_KEYRING env var)
            credentials: Service account credentials (JSON string, dict, or path to JSON file)
            use_workload_identity: Use GCP metadata service for authentication
            default_algorithm: Default signing algorithm
            timeout: HTTP request timeout in seconds
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT', '')
        self.location = location or os.getenv('GCP_LOCATION', '')
        self.key_ring = key_ring or os.getenv('GCP_KEYRING', '')
        self.credentials = credentials
        self.use_workload_identity = use_workload_identity
        self.default_algorithm = default_algorithm
        self.timeout = timeout


class GcpKmsSigner(SignerBackend):
    """Google Cloud KMS Signer Backend"""
    
    def __init__(self, config: GcpKmsSignerConfig):
        """Initialize GCP KMS signer"""
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expiry: int = 0
    
    def get_name(self) -> str:
        """Get backend name"""
        return 'Google Cloud KMS'
    
    def is_available(self) -> bool:
        """Check if backend is available"""
        if self.config.use_workload_identity:
            # Workload identity always available in GCP environment
            return True
        return bool(self.config.credentials) and bool(self.config.project_id)
    
    def sign(self, request: SignRequest) -> SignResponse:
        """Sign a message using GCP KMS"""
        if not self.is_available():
            raise ValueError(
                'GCP KMS signer not configured. Set GCP_PROJECT, GCP_LOCATION, GCP_KEYRING environment variables '
                'or provide credentials. For production use, install google-cloud-kms: pip install google-cloud-kms'
            )
        
        # Get access token
        access_token = self._get_access_token()
        
        # Map algorithm to GCP format
        algorithm = self._map_algorithm(request.algorithm or self.config.default_algorithm)
        
        # Build key resource name
        # Format: projects/{project}/locations/{location}/keyRings/{keyRing}/cryptoKeys/{keyName}
        if '/' in request.key_id:
            key_name = request.key_id
        else:
            key_name = (
                f'projects/{self.config.project_id}/'
                f'locations/{self.config.location}/'
                f'keyRings/{self.config.key_ring}/'
                f'cryptoKeys/{request.key_id}'
            )
        
        # GCP KMS API endpoint
        url = f'https://cloudkms.googleapis.com/v1/{key_name}:asymmetricSign'
        
        # Base64 encode message digest
        message_base64 = base64.b64encode(request.message).decode('utf-8')
        
        request_body = {
            'digest': {
                'sha256': message_base64,  # GCP expects digest, not raw message
            },
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        
        try:
            response = requests.post(url, json=request_body, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'signature' not in data:
                raise RuntimeError('GCP KMS sign response missing signature')
            
            # GCP returns signature as base64 string
            signature = base64.b64decode(data['signature'])
            
            return SignResponse(
                signature=signature,
                key_id=request.key_id,
                algorithm=algorithm,
                metadata={
                    'name': data.get('name'),
                    'verified_digest_crc32c': data.get('verifiedDigestCrc32c'),
                },
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f'GCP KMS sign failed: {e}') from e
    
    def _get_access_token(self) -> str:
        """Get GCP access token"""
        import time
        # Check if token is still valid (with 5 minute buffer)
        if self._access_token and time.time() < (self._token_expiry - 300):
            return self._access_token
        
        if self.config.use_workload_identity:
            # Use GCP metadata service
            metadata_url = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token'
            
            response = requests.get(
                metadata_url,
                headers={'Metadata-Flavor': 'Google'},
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            
            import time
            data = response.json()
            self._access_token = data['access_token']
            self._token_expiry = int(time.time()) + data.get('expires_in', 3600)
            
            return data['access_token']
        else:
            # Use service account credentials
            if not self.config.credentials:
                raise ValueError('GCP credentials not configured')
            
            # Service account authentication requires JWT signing
            # For production use, install google-cloud-kms package:
            # pip install google-cloud-kms
            # Then use: from google.cloud import kms; client = kms.KeyManagementServiceClient(credentials=...)
            #
            # For now, we support workload identity which is the recommended approach for GCP environments
            raise ValueError(
                'Service account authentication requires google-cloud-kms SDK. '
                'Install it with: pip install google-cloud-kms. '
                'Alternatively, use workload identity (recommended for GCP environments).'
            )
    
    def _map_algorithm(self, algorithm: str) -> str:
        """Map algorithm string to GCP format"""
        algorithm_map = {
            'ECDSA_SHA_256': 'EC_SIGN_P256_SHA256',
            'ECDSA_SHA_384': 'EC_SIGN_P384_SHA384',
            'ECDSA_SHA_512': 'EC_SIGN_P512_SHA512',
            'RSASSA_PSS_SHA_256': 'RSA_SIGN_PSS_2048_SHA256',
            'RSASSA_PSS_SHA_384': 'RSA_SIGN_PSS_3072_SHA256',
            'RSASSA_PSS_SHA_512': 'RSA_SIGN_PSS_4096_SHA256',
            'RSASSA_PKCS1_V1_5_SHA_256': 'RSA_SIGN_PKCS1_2048_SHA256',
            'RSASSA_PKCS1_V1_5_SHA_384': 'RSA_SIGN_PKCS1_3072_SHA256',
            'RSASSA_PKCS1_V1_5_SHA_512': 'RSA_SIGN_PKCS1_4096_SHA256',
        }
        
        # If already in GCP format, return as-is
        if algorithm.startswith('EC_SIGN_') or algorithm.startswith('RSA_SIGN_'):
            return algorithm
        
        return algorithm_map.get(algorithm.upper(), 'EC_SIGN_P256_SHA256')

