"""Time-ordered ID generation utilities."""

import secrets
import time


def generate_id(prefix: str) -> str:
    """Generate a time-ordered unique ID.

    Format: {prefix}_{timestamp}_{random}

    Args:
        prefix: Type prefix (e.g., "msg", "conv", "part")

    Returns:
        Unique ID string

    Example:
        >>> generate_id("msg")
        'msg_20260131_142305_abc123'
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(3)
    return f"{prefix}_{timestamp}_{random_suffix}"
