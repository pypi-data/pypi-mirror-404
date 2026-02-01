"""
Gate SDK - Utility Functions

Canonical JSON serialization and other utilities.
"""

import json
from typing import Any, Dict, List, Union


def canonical_json(obj: Any) -> bytes:
    """
    Canonicalize JSON by sorting keys recursively and removing whitespace.

    Rules:
    - All keys sorted alphabetically (case-sensitive)
    - No whitespace between tokens
    - UTF-8 encoding
    - Stable ordering for arrays and nested objects

    Args:
        obj: Object to canonicalize

    Returns:
        Canonical JSON bytes (no whitespace, sorted keys)
    """
    def sort_keys_recursive(item: Any) -> Any:
        if isinstance(item, dict):
            return {k: sort_keys_recursive(item[k]) for k in sorted(item.keys())}
        elif isinstance(item, list):
            return [sort_keys_recursive(i) for i in item]
        else:
            return item

    sorted_obj = sort_keys_recursive(obj)
    return json.dumps(
        sorted_obj,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")


def sha256_hex(data: Union[str, bytes]) -> str:
    """
    Compute SHA256 hash and return as hex string.

    Args:
        data: Input data (string or bytes)

    Returns:
        SHA256 hash as hex string (64 characters)
    """
    import hashlib

    if isinstance(data, str):
        data = data.encode("utf-8")

    return hashlib.sha256(data).hexdigest()


def clamp(value: int, min_val: int, max_val: int) -> int:
    """
    Clamp a value between min and max.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def now_ms() -> int:
    """
    Get current timestamp in milliseconds.

    Returns:
        Unix timestamp in milliseconds
    """
    import time
    return int(time.time() * 1000)


def now_epoch_seconds() -> int:
    """
    Get current timestamp in seconds (epoch).

    Returns:
        Unix timestamp in seconds
    """
    import time
    return int(time.time())

