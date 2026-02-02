"""Authenticated client utilities for CLI commands.

Provides a helper to get an TerminalUse client with stored credentials.
"""

from __future__ import annotations

import typer

from terminaluse import TerminalUse
from terminaluse.lib.cli.utils.credentials import (
    get_stored_token,
    has_refresh_token,
    is_authenticated,
    is_token_expired,
    refresh_credentials,
)


class AuthenticationRequired(typer.Exit):
    """Raised when authentication is required but not available."""

    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(code=1)


def get_authenticated_client() -> TerminalUse:
    """Get an TerminalUse client with stored credentials.

    If the token is expired but a refresh token is available, attempts to
    refresh the credentials automatically.

    Returns:
        TerminalUse client configured with the stored session token.

    Raises:
        AuthenticationRequired: If not authenticated or token refresh failed.
    """
    from rich.console import Console

    console = Console()

    # Check if we have any credentials at all (regardless of expiration)
    token = get_stored_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Run 'tu login' first.")
        raise AuthenticationRequired("Not authenticated")

    # Try to refresh if token is expired
    if is_token_expired():
        if has_refresh_token() and refresh_credentials():
            # Silently refreshed, get the new token
            token = get_stored_token()
        else:
            console.print("[red]Error:[/red] Session expired. Run 'tu login' to re-authenticate.")
            raise AuthenticationRequired("Session expired")

    return TerminalUse(token=token)
