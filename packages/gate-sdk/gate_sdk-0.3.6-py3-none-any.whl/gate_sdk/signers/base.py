"""
Signer Backend Base Interface

Abstract interface for cryptographic signing backends (AWS KMS, HashiCorp Vault, GCP KMS, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class SignRequest:
    """Sign request"""
    
    key_id: str
    """Key identifier (KMS key ID, Vault key name, GCP key name, etc.)"""
    
    message: bytes
    """Message to sign (raw bytes)"""
    
    algorithm: Optional[str] = None
    """Signing algorithm (backend-specific)"""
    
    message_type: Optional[str] = None
    """Message type (RAW, DIGEST, etc.)"""
    
    options: Optional[Dict[str, Any]] = None
    """Additional backend-specific options"""


@dataclass
class SignResponse:
    """Sign response"""
    
    signature: bytes
    """Signature bytes"""
    
    key_id: str
    """Key ID used for signing"""
    
    algorithm: str
    """Signing algorithm used"""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata"""


class SignerBackend(ABC):
    """Signer Backend Interface
    
    All signing backends must implement this interface.
    """
    
    @abstractmethod
    def sign(self, request: SignRequest) -> SignResponse:
        """Sign a message
        
        Args:
            request: Sign request
            
        Returns:
            Sign response with signature
            
        Raises:
            ValueError: If backend is not configured
            RuntimeError: If signing fails
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get backend name for logging"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available/configured"""
        pass

