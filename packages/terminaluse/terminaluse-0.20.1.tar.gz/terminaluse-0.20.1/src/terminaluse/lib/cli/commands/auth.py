"""Authentication commands for tu CLI.

Provides login, logout, and whoami commands for managing CLI authentication.
Uses OAuth 2.0 PKCE flow for browser-based authentication.
"""

from __future__ import annotations

import sys
import webbrowser
from datetime import datetime, timedelta

import questionary
import typer
from rich.console import Console
from rich.table import Table

from terminaluse import TerminalUse
from terminaluse.lib.cli.utils.callback_server import CallbackServer
from terminaluse.lib.cli.utils.credentials import (
    clear_credentials,
    get_credentials_info,
    has_refresh_token,
    is_authenticated,
    is_token_expired,
    refresh_credentials,
    store_credentials,
)
from terminaluse.lib.cli.utils.pkce import (
    generate_code_challenge,
    generate_code_verifier,
)
from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)
console = Console()


def _get_unauthenticated_client() -> TerminalUse:
    """Get a TerminalUse client without authentication for OAuth endpoints."""
    return TerminalUse(token=None, agent_api_key=None)


def login(
    token: str | None = typer.Option(
        None,
        "--token",
        "-t",
        help="API token for manual entry (bypasses browser flow)",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Use manual token entry instead of browser-based login",
    ),
    timeout: int = typer.Option(
        120,
        "--timeout",
        help="Timeout in seconds for browser authentication",
    ),
) -> None:
    """Authenticate with the tu platform using OAuth.

    Opens your browser to complete authentication. For headless environments
    or CI/CD, use --no-browser to enter a token manually.
    """
    # Check if already authenticated
    if is_authenticated() and not is_token_expired():
        creds_info = get_credentials_info()
        if creds_info and creds_info.get("email"):
            console.print(f"[yellow]Already logged in as {creds_info['email']}[/yellow]")
        else:
            console.print("[yellow]Already logged in[/yellow]")

        # In non-interactive mode, don't prompt - just continue with new login
        if sys.stdin.isatty():
            proceed = questionary.confirm("Do you want to log in with a different account?").ask()
            if not proceed:
                # User wants to keep current account - try to refresh the token
                if has_refresh_token():
                    if refresh_credentials():
                        raise typer.Exit(0)
                    # Refresh failed, fall through to fresh login
                else:
                    console.print("Login cancelled")
                    raise typer.Exit(0)

    # Manual token entry mode
    if no_browser or token:
        _manual_token_login(token)
        return

    # Browser-based OAuth login
    _browser_oauth_login(timeout)


def _manual_token_login(token: str | None) -> None:
    """Handle manual token entry for headless environments."""
    if not token:
        if not sys.stdin.isatty():
            console.print("[red]Error:[/red] --token is required in non-interactive mode.")
            console.print("Usage: tu login --no-browser --token YOUR_TOKEN")
            raise typer.Exit(1)
        console.print("Enter your API token from https://app.terminaluse.com/settings/api-keys\n")
        token = questionary.password("API Token:").ask()
        if not token:
            console.print("[red]Login cancelled[/red]")
            raise typer.Exit(1)

    # Store the token
    store_credentials(token=token)
    console.print("\n[green]Successfully logged in![/green]")
    console.print("Credentials stored at ~/.terminaluse/credentials.json")


def _get_authorization_url(redirect_uri: str, code_challenge: str) -> tuple[str, str]:
    """Get the WorkOS authorization URL from the API.

    Returns:
        Tuple of (authorization_url, state)
    """
    client = _get_unauthenticated_client()
    try:
        response = client.o_auth.initiate_oauth(
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
        )
        return response.authorization_url, response.state
    except Exception as e:
        raise RuntimeError(f"Failed to initiate OAuth: {e}") from e


def _browser_oauth_login(timeout: int) -> None:
    """Handle browser-based OAuth PKCE login via WorkOS."""
    # Generate PKCE parameters
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    console.print("[dim]Initiating authentication...[/dim]")

    # Start callback server first to lock the port, then request auth URL
    # with the actual bound port. This avoids a mismatch if the default port is taken.
    try:
        server = CallbackServer()
        server_port = server.port
    except RuntimeError as e:
        console.print(f"\n[red]Failed to start callback server:[/red] {str(e)}")
        raise typer.Exit(1)

    redirect_uri = f"http://127.0.0.1:{server_port}/callback"

    try:
        auth_url, expected_state = _get_authorization_url(redirect_uri, code_challenge)
    except Exception as e:
        console.print(f"\n[red]Failed to initiate login:[/red] {str(e)}")
        raise typer.Exit(1)

    server.expected_state = expected_state

    try:
        with server:
            # Open browser
            console.print("Opening browser for authentication...")
            console.print(f"\n[dim]If browser doesn't open, visit:[/dim]\n{auth_url}\n")

            if not webbrowser.open(auth_url):
                console.print("[yellow]Could not open browser automatically.[/yellow]")
                console.print("Please open the URL above in your browser.")

            # Wait for callback
            console.print("Waiting for authorization...")
            with console.status("[bold]Waiting for browser authentication..."):
                result = server.wait_for_callback(timeout=timeout)

            if result.error:
                error_msg = result.error_description or result.error
                console.print(f"\n[red]Authorization failed:[/red] {error_msg}")
                raise typer.Exit(1)

            if not result.code:
                console.print("[red]No authorization code received[/red]")
                raise typer.Exit(1)

            # Exchange code for tokens
            console.print("[dim]Exchanging authorization code for tokens...[/dim]")
            tokens = _exchange_code_for_tokens(
                code=result.code,
                code_verifier=code_verifier,
                redirect_uri=redirect_uri,
            )

        # Calculate expiration
        expires_at = None
        if tokens.get("expires_in"):
            expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])

        # Store credentials
        store_credentials(
            token=tokens["session_jwt"],
            refresh_token=tokens.get("refresh_token"),
            member_id=tokens.get("member_id"),
            org_id=tokens.get("org_id"),
            email=tokens.get("email"),
            name=tokens.get("name"),
            expires_at=expires_at,
        )

        console.print("\n[green]Successfully logged in![/green]")
        if tokens.get("email"):
            console.print(f"Logged in as: {tokens['email']}")
        console.print("Credentials stored at ~/.terminaluse/credentials.json")

    except TimeoutError:
        console.print("\n[red]Timed out waiting for authorization.[/red]")
        console.print("Please try again or use --no-browser for manual token entry.")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]Login failed:[/red] {str(e)}")
        logger.exception("OAuth login failed")
        raise typer.Exit(1)


def _exchange_code_for_tokens(
    code: str,
    code_verifier: str,
    redirect_uri: str,  # Not used by SDK but kept for interface compatibility
) -> dict:
    """Exchange authorization code for tokens."""
    client = _get_unauthenticated_client()
    try:
        response = client.cli_authentication.exchange_cli_token(
            code=code,
            code_verifier=code_verifier,
        )
        # Convert Pydantic model to dict for compatibility with existing code
        return {
            "session_jwt": response.session_jwt,
            "refresh_token": response.refresh_token,
            "expires_in": response.expires_in,
            "email": response.email,
            "member_id": response.member_id,
            "org_id": response.org_id,
            "name": response.name,
        }
    except Exception as e:
        raise RuntimeError(f"Token exchange failed: {e}") from e


def logout() -> None:
    """Log out and clear stored credentials."""
    if not is_authenticated():
        console.print("[yellow]Not currently logged in[/yellow]")
        raise typer.Exit(0)

    clear_credentials()
    console.print("[green]Successfully logged out[/green]")
    console.print("Credentials removed from ~/.terminaluse/credentials.json")


def whoami(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show current authentication status and user info."""
    import json

    from terminaluse.lib.cli.utils.credentials import get_stored_credentials

    creds = get_stored_credentials()
    if not creds:
        if json_output:
            typer.echo(json.dumps({"authenticated": False}))
        else:
            console.print("[yellow]Not logged in[/yellow]")
            console.print("\nRun 'tu login' to authenticate")
        raise typer.Exit(0)

    creds_info = get_credentials_info()
    if creds_info is None:
        if json_output:
            typer.echo(json.dumps({"error": "Error reading credentials"}))
        else:
            console.print("[red]Error reading credentials[/red]")
        raise typer.Exit(1)

    if json_output:
        output = {
            "authenticated": True,
            "email": creds_info.get("email"),
            "name": creds_info.get("name"),
            "member_id": creds_info.get("member_id"),
            "org_id": creds_info.get("org_id"),
            "created_at": creds_info.get("created_at"),
            "expires_at": creds_info.get("expires_at"),
            "expired": is_token_expired(),
        }
        typer.echo(json.dumps(output, default=str))
        return

    console.print("[bold blue]Current Authentication[/bold blue]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    if creds_info.get("email"):
        table.add_row("Email", creds_info["email"])
    if creds_info.get("name"):
        table.add_row("Name", creds_info["name"])
    if creds_info.get("member_id"):
        table.add_row("Member ID", creds_info["member_id"])
    if creds_info.get("org_id"):
        table.add_row("Organization", creds_info["org_id"])
    table.add_row("Token", creds_info["token"])
    if creds_info.get("created_at"):
        table.add_row("Logged in", creds_info["created_at"])
    if creds_info.get("expires_at"):
        table.add_row("Expires", creds_info["expires_at"])

    console.print(table)

    # Check if token is expired and try to refresh
    if is_token_expired():
        from terminaluse.lib.cli.utils.credentials import has_refresh_token, refresh_credentials

        if has_refresh_token():
            if not refresh_credentials():
                console.print("\n[yellow]Session expired[/yellow]")
                console.print("Run 'tu login' to authenticate again")
        else:
            console.print("\n[yellow]Session expired[/yellow]")
            console.print("Run 'tu login' to authenticate again")
