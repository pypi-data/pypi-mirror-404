"""
HashiCorp Vault Signer Backend

Implements SignerBackend for HashiCorp Vault Transit Engine
"""

import os
import base64
import requests
from typing import Optional, Dict, Any

from .base import SignerBackend, SignRequest, SignResponse


class VaultSignerConfig:
    """Vault signer configuration"""
    
    def __init__(
        self,
        vault_url: Optional[str] = None,  # From VAULT_ADDR env var if not provided
        token: Optional[str] = None,  # From VAULT_TOKEN env var if not provided
        app_role: Optional[Dict[str, str]] = None,  # {role_id: str, secret_id: str}
        mount_path: str = 'transit',
        default_algorithm: str = 'ecdsa-sha2-256',
        timeout: int = 5,
    ):
        """
        Initialize Vault signer config.
        
        Args:
            vault_url: Vault API base URL (default: VAULT_ADDR env var)
            token: Vault authentication token (default: VAULT_TOKEN env var)
            app_role: AppRole authentication {role_id, secret_id}
            mount_path: Transit engine mount path (default: 'transit')
            default_algorithm: Default signing algorithm
            timeout: HTTP request timeout in seconds
        """
        self.vault_url = vault_url or os.getenv('VAULT_ADDR', '')
        self.token = token or os.getenv('VAULT_TOKEN', '')
        self.app_role = app_role
        self.mount_path = mount_path
        self.default_algorithm = default_algorithm
        self.timeout = timeout


class VaultSigner(SignerBackend):
    """HashiCorp Vault Signer Backend"""
    
    def __init__(self, config: VaultSignerConfig):
        """Initialize Vault signer"""
        self.config = config
        self._auth_token: Optional[str] = None
    
    def get_name(self) -> str:
        """Get backend name"""
        return 'HashiCorp Vault'
    
    def is_available(self) -> bool:
        """Check if backend is available"""
        return bool(self.config.vault_url) and (bool(self.config.token) or bool(self.config.app_role))
    
    def sign(self, request: SignRequest) -> SignResponse:
        """Sign a message using Vault Transit Engine"""
        if not self.is_available():
            raise ValueError('Vault signer not configured. Set VAULT_ADDR and VAULT_TOKEN environment variables.')
        
        # Authenticate if needed (AppRole)
        if not self._auth_token and self.config.app_role:
            self._authenticate_app_role()
        
        token = self.config.token or self._auth_token
        if not token:
            raise ValueError('Vault authentication token not available')
        
        # Map algorithm to Vault format
        algorithm = self._map_algorithm(request.algorithm or self.config.default_algorithm)
        
        # Vault Transit Engine sign endpoint
        url = f'{self.config.vault_url}/v1/{self.config.mount_path}/sign/{request.key_id}'
        
        # Base64 encode message
        message_base64 = base64.b64encode(request.message).decode('utf-8')
        
        request_body = {
            'input': message_base64,
            **({'algorithm': algorithm} if algorithm else {}),
            **(request.options or {}),
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Vault-Token': token,
        }
        
        try:
            response = requests.post(url, json=request_body, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or 'signature' not in data['data']:
                raise RuntimeError('Vault sign response missing signature')
            
            # Vault returns signature in format: vault:v1:base64signature
            # Extract the base64 signature
            signature_str = data['data']['signature']
            signature_parts = signature_str.split(':')
            signature_base64 = signature_parts[-1]
            signature = base64.b64decode(signature_base64)
            
            return SignResponse(
                signature=signature,
                key_id=request.key_id,
                algorithm=algorithm,
                metadata={
                    'vault_signature': signature_str,
                    'key_version': data['data'].get('key_version'),
                },
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f'Vault sign failed: {e}') from e
    
    def _authenticate_app_role(self) -> None:
        """Authenticate using AppRole"""
        if not self.config.app_role:
            raise ValueError('AppRole not configured')
        
        url = f'{self.config.vault_url}/v1/auth/approle/login'
        
        response = requests.post(
            url,
            json={
                'role_id': self.config.app_role['role_id'],
                'secret_id': self.config.app_role['secret_id'],
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'auth' not in data or 'client_token' not in data['auth']:
            raise RuntimeError('Vault AppRole authentication response missing token')
        
        self._auth_token = data['auth']['client_token']
    
    def _map_algorithm(self, algorithm: str) -> str:
        """Map algorithm string to Vault format"""
        algorithm_map = {
            'ECDSA_SHA_256': 'ecdsa-sha2-256',
            'ECDSA_SHA_384': 'ecdsa-sha2-384',
            'ECDSA_SHA_512': 'ecdsa-sha2-512',
            'RSASSA_PSS_SHA_256': 'rsa-sha2-256',
            'RSASSA_PSS_SHA_384': 'rsa-sha2-384',
            'RSASSA_PSS_SHA_512': 'rsa-sha2-512',
        }
        
        # If already in Vault format, return as-is
        if algorithm.startswith('ecdsa-') or algorithm.startswith('rsa-'):
            return algorithm
        
        return algorithm_map.get(algorithm.upper(), 'ecdsa-sha2-256')

