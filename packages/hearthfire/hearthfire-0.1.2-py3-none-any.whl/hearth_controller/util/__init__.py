"""
Utility functions for hearth-controller.
"""

import secrets


def generate_id(length: int = 16) -> str:
    """
    Generate a URL-safe random ID.

    Args:
        length: Number of random bytes (default 16, produces ~22 char string)

    Returns:
        URL-safe base64 string (no padding)
    """
    return secrets.token_urlsafe(length)[:22]
