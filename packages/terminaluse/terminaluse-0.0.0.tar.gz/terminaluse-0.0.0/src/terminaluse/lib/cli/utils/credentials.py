"""Credential storage utilities for CLI authentication.

Manages persistent storage of authentication tokens at ~/.terminaluse/credentials.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Default credentials location
CREDENTIALS_FILE = Path.home() / ".terminaluse" / "credentials.json"


@dataclass
class StoredCredentials:
    """Stored authentication credentials."""

    token: str
    refresh_token: str | None = None
    user_id: str | None = None
    email: str | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    # OAuth-specific fields
    member_id: str | None = None
    org_id: str | None = None
    name: str | None = None


def get_credentials_path() -> Path:
    """Get the path to the credentials file.

    Can be overridden via TERMINALUSE_CREDENTIALS_FILE environment variable.
    """
    env_path = os.environ.get("TERMINALUSE_CREDENTIALS_FILE")
    if env_path:
        return Path(env_path)
    return CREDENTIALS_FILE


def get_stored_token() -> str | None:
    """Read auth token from credentials file.

    Returns:
        The stored token string, or None if not found/invalid
    """
    credentials = get_stored_credentials()
    if credentials:
        return credentials.token
    return None


def get_stored_credentials() -> StoredCredentials | None:
    """Read full credentials from storage.

    Returns:
        StoredCredentials object, or None if not found/invalid
    """
    creds_file = get_credentials_path()

    if not creds_file.exists():
        return None

    try:
        data = json.loads(creds_file.read_text())

        # Parse optional datetime fields
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return StoredCredentials(
            token=data["token"],
            refresh_token=data.get("refresh_token"),
            user_id=data.get("user_id"),
            email=data.get("email"),
            expires_at=expires_at,
            created_at=created_at,
            member_id=data.get("member_id"),
            org_id=data.get("org_id"),
            name=data.get("name"),
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def store_credentials(
    token: str,
    refresh_token: str | None = None,
    user_id: str | None = None,
    email: str | None = None,
    expires_at: datetime | None = None,
    member_id: str | None = None,
    org_id: str | None = None,
    name: str | None = None,
) -> None:
    """Store authentication credentials.

    Args:
        token: The authentication token (session JWT)
        refresh_token: Optional refresh token for obtaining new access tokens
        user_id: Optional user ID
        email: Optional user email
        expires_at: Optional token expiration time
        member_id: Optional Stytch member ID
        org_id: Optional Stytch organization ID
        name: Optional user display name
    """
    creds_dir = get_credentials_path().parent
    creds_file = get_credentials_path()

    # Create directory if needed
    creds_dir.mkdir(parents=True, exist_ok=True)

    # Build credentials data
    data: dict[str, Any] = {
        "token": token,
        "created_at": datetime.now().isoformat(),
    }

    if refresh_token:
        data["refresh_token"] = refresh_token
    if user_id:
        data["user_id"] = user_id
    if email:
        data["email"] = email
    if expires_at:
        data["expires_at"] = expires_at.isoformat()
    if member_id:
        data["member_id"] = member_id
    if org_id:
        data["org_id"] = org_id
    if name:
        data["name"] = name

    # Write credentials with secure permissions
    creds_file.write_text(json.dumps(data, indent=2))

    # Set restrictive permissions (owner read/write only)
    try:
        creds_file.chmod(0o600)
    except OSError:
        # Windows doesn't support chmod the same way, ignore
        pass


def clear_credentials() -> None:
    """Remove stored credentials."""
    creds_file = get_credentials_path()
    if creds_file.exists():
        creds_file.unlink()


def is_authenticated() -> bool:
    """Check if valid credentials are stored.

    Returns:
        True if credentials exist and haven't expired
    """
    credentials = get_stored_credentials()
    if not credentials:
        return False

    # Check expiration if set
    if credentials.expires_at:
        if datetime.now() >= credentials.expires_at:
            return False

    return True


def get_credentials_info() -> dict[str, Any] | None:
    """Get credential info for display (without exposing full token).

    Returns:
        Dict with masked token and metadata, or None if not authenticated
    """
    credentials = get_stored_credentials()
    if not credentials:
        return None

    # Mask the token for display
    token = credentials.token
    if len(token) > 8:
        masked_token = f"{token[:4]}...{token[-4:]}"
    else:
        masked_token = "****"

    return {
        "token": masked_token,
        "user_id": credentials.user_id,
        "email": credentials.email,
        "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
        "created_at": credentials.created_at.isoformat() if credentials.created_at else None,
        "member_id": credentials.member_id,
        "org_id": credentials.org_id,
        "name": credentials.name,
    }


def is_token_expired() -> bool:
    """Check if the stored token has expired.

    Returns:
        True if token is expired or doesn't exist, False otherwise
    """
    credentials = get_stored_credentials()
    if not credentials:
        return True

    if not credentials.expires_at:
        return False  # No expiration set, assume valid

    # Add 60 second buffer before expiration
    return datetime.now() >= (credentials.expires_at - timedelta(seconds=60))


def has_refresh_token() -> bool:
    """Check if a refresh token is available.

    Returns:
        True if a refresh token is stored, False otherwise
    """
    credentials = get_stored_credentials()
    return credentials is not None and credentials.refresh_token is not None


def get_refresh_token() -> str | None:
    """Get the stored refresh token.

    Returns:
        The refresh token string, or None if not found
    """
    credentials = get_stored_credentials()
    if credentials:
        return credentials.refresh_token
    return None


def refresh_credentials() -> bool:
    """Refresh the stored credentials using the refresh token.

    Calls the SDK's cli_authentication.refresh_cli_token endpoint with the stored
    refresh token and updates the stored credentials with the new tokens.

    Returns:
        True if refresh succeeded, False otherwise
    """
    from terminaluse import TerminalUse

    credentials = get_stored_credentials()
    if not credentials or not credentials.refresh_token:
        return False

    try:
        # Use SDK client without auth for refresh endpoint
        client = TerminalUse(token=None, agent_api_key=None)
        response = client.cli_authentication.refresh_cli_token(
            refresh_token=credentials.refresh_token,
        )

        # Calculate new expiration
        expires_at = None
        if response.expires_in:
            expires_at = datetime.now() + timedelta(seconds=response.expires_in)

        # Update stored credentials with new tokens
        # Preserve existing metadata (email, name, etc.)
        store_credentials(
            token=response.session_jwt,
            refresh_token=response.refresh_token,
            user_id=credentials.user_id,
            email=credentials.email,
            expires_at=expires_at,
            member_id=credentials.member_id,
            org_id=credentials.org_id,
            name=credentials.name,
        )

        return True

    except Exception:
        return False
