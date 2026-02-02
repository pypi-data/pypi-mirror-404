"""PKCE utilities for OAuth 2.0 Authorization Code flow.

Implements RFC 7636 - Proof Key for Code Exchange.
"""

from __future__ import annotations

import base64
import hashlib
import secrets


def generate_code_verifier(length: int = 64) -> str:
    """
    Generate a cryptographically random code verifier.

    Per RFC 7636, the code verifier must be between 43 and 128 characters.

    Args:
        length: Length of the verifier (43-128 characters, default 64)

    Returns:
        URL-safe base64-encoded random string

    Raises:
        ValueError: If length is not in valid range
    """
    if not (43 <= length <= 128):
        raise ValueError("Code verifier length must be between 43 and 128")

    # Generate random bytes and encode as URL-safe base64
    # We need extra bytes since base64 encoding expands the size
    random_bytes = secrets.token_bytes(length)
    verifier = base64.urlsafe_b64encode(random_bytes).decode("utf-8")

    # Trim to exact length and remove padding
    return verifier[:length].rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    """
    Generate a code challenge from the code verifier using S256 method.

    Per RFC 7636, S256 is the recommended method:
    code_challenge = BASE64URL(SHA256(code_verifier))

    Args:
        code_verifier: The code verifier string

    Returns:
        Base64 URL-encoded SHA256 hash of the verifier (without padding)
    """
    # SHA256 hash of the verifier
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()

    # Base64 URL-encode and remove padding
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    return challenge


def generate_state(length: int = 32) -> str:
    """
    Generate a random state parameter for CSRF protection.

    Args:
        length: Number of random bytes (default 32, resulting in 64 hex chars)

    Returns:
        Random hex string
    """
    return secrets.token_hex(length)


