"""
BlockIntel Gate SDK for Python

A Python SDK for integrating BlockIntel Gate hot-path defense into your applications.
"""

from .client import BlockIntelGateClient
from .auth_hmac import HmacAuthProvider
from .exceptions import BlockIntelGateError, BlockIntelGateAuthError, BlockIntelGateDecisionError

__version__ = "1.0.0"

__all__ = [
    "BlockIntelGateClient",
    "HmacAuthProvider",
    "BlockIntelGateError",
    "BlockIntelGateAuthError",
    "BlockIntelGateDecisionError",
]

