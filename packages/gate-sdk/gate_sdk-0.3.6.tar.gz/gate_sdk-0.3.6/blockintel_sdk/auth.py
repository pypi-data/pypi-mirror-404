"""
Authentication Provider

Simple auth provider interface for API key management.
"""

from typing import Callable, Optional


AuthProvider = Callable[[], str]


def create_api_key_provider(api_key: str) -> AuthProvider:
    """
    Create a simple API key provider.

    Args:
        api_key: API key string

    Returns:
        Auth provider function
    """
    return lambda: api_key

