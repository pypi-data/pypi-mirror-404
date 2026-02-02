"""
Thin wrapper around Fern-generated clients to provide:
1. TERMINALUSE_BASE_URL environment variable support
2. TerminalUse/AsyncTerminalUse class names (matching Stainless SDK)
3. Flexible auth (allows token OR agent_api_key, not requiring both)
4. Automatic token refresh on expiration (when credentials are available)
"""

from __future__ import annotations

import logging
import os
import typing

import httpx

from .client import AsyncTerminaluseApi, TerminaluseApi

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.terminaluse.com"


def _create_auto_refresh_token_getter(initial_token: str | None) -> typing.Callable[[], str]:
    """Create a token getter that automatically refreshes expired tokens.

    This function returns a callable that:
    1. Returns the current stored token
    2. If the token appears expired, attempts to refresh it using stored credentials
    3. Falls back to the current token if refresh fails

    The refresh is done proactively when the token is fetched, not reactively after a 401.
    """
    # Use a mutable container to allow updating the token
    token_state: dict[str, str | float] = {"token": initial_token or "", "last_check": 0.0}

    def get_token() -> str:
        import time

        current_time = time.time()

        # Only check every 30 seconds to avoid overhead
        if current_time - float(token_state["last_check"]) < 30:
            return str(token_state["token"])

        token_state["last_check"] = current_time

        try:
            from terminaluse.lib.cli.utils.credentials import (
                get_stored_token,
                has_refresh_token,
                is_token_expired,
                refresh_credentials,
            )

            # If the stored token has changed (e.g., user logged in again), update
            stored_token = get_stored_token()
            if stored_token and stored_token != token_state["token"]:
                token_state["token"] = stored_token

            # Check if we need to refresh
            if is_token_expired() and has_refresh_token():
                log.debug("Token expired, attempting refresh...")
                if refresh_credentials():
                    new_token = get_stored_token()
                    if new_token:
                        token_state["token"] = new_token
                        log.info("Token refreshed successfully")
                        try:
                            from rich.console import Console

                            Console(stderr=True).print(
                                "[dim]Session expired, token refreshed automatically[/dim]"
                            )
                        except ImportError:
                            pass
                else:
                    log.debug("Token refresh failed")

        except ImportError:
            # CLI utilities not available (e.g., minimal install)
            pass
        except Exception as e:
            log.debug(f"Error during token refresh check: {e}")

        return str(token_state["token"])

    return get_token


class TerminalUse(TerminaluseApi):
    """
    Synchronous client for the TerminalUse API.

    This is a thin wrapper around TerminaluseApi that:
    - Reads TERMINALUSE_BASE_URL from environment (with fallback to default)
    - Allows flexible auth (token OR agent_api_key, not requiring both)
    - Optionally auto-refreshes expired tokens using stored credentials

    Parameters
    ----------
    base_url : str, optional
        The base URL for the API. Defaults to TERMINALUSE_BASE_URL env var,
        or https://api.terminaluse.com if not set.

    token : str, optional
        Bearer token for user authentication. Defaults to TERMINALUSE_API_KEY env var.

    agent_api_key : str, optional
        API key for agent authentication. Defaults to TERMINALUSE_AGENT_API_KEY env var.

    headers : dict, optional
        Additional headers to send with every request.

    timeout : float, optional
        Request timeout in seconds. Defaults to 60.

    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to True.

    httpx_client : httpx.Client, optional
        Custom httpx client for making requests.

    auto_refresh_token : bool, optional
        Enable automatic token refresh on expiration. When enabled, the client
        will attempt to refresh expired tokens using stored credentials.
        Defaults to True.

    Examples
    --------
    >>> from terminaluse import TerminalUse
    >>> client = TerminalUse()  # Uses env vars
    >>> client = TerminalUse(token="my-token")  # User auth
    >>> client = TerminalUse(agent_api_key="my-key")  # Agent auth
    """

    def __init__(
        self,
        *,
        base_url: typing.Optional[str] = None,
        token: typing.Optional[typing.Union[str, typing.Callable[[], str]]] = None,
        agent_api_key: typing.Optional[str] = None,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        timeout: typing.Optional[float] = None,
        follow_redirects: typing.Optional[bool] = True,
        httpx_client: typing.Optional[httpx.Client] = None,
        auto_refresh_token: bool = True,
    ):
        # Handle base_url from env var
        if base_url is None:
            base_url = os.getenv("TERMINALUSE_BASE_URL", DEFAULT_BASE_URL)

        # Handle auth - read from env vars if not provided
        if token is None:
            token = os.getenv("TERMINALUSE_API_KEY")
        if agent_api_key is None:
            agent_api_key = os.getenv("TERMINALUSE_AGENT_API_KEY")

        # If auto_refresh_token is enabled and token is a string, wrap it in auto-refresh logic
        final_token: typing.Union[str, typing.Callable[[], str]]
        if auto_refresh_token and isinstance(token, str):
            final_token = _create_auto_refresh_token_getter(token)
        elif token:
            final_token = token
        else:
            final_token = ""

        # Fern requires both to be non-None, so use empty string as fallback
        # The backend handles missing auth headers gracefully
        super().__init__(
            base_url=base_url,
            token=final_token,
            agent_api_key=agent_api_key if agent_api_key else "",
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            httpx_client=httpx_client,
        )


class AsyncTerminalUse(AsyncTerminaluseApi):
    """
    Asynchronous client for the TerminalUse API.

    This is a thin wrapper around AsyncTerminaluseApi that:
    - Reads TERMINALUSE_BASE_URL from environment (with fallback to default)
    - Allows flexible auth (token OR agent_api_key, not requiring both)
    - Optionally auto-refreshes expired tokens using stored credentials

    Parameters
    ----------
    base_url : str, optional
        The base URL for the API. Defaults to TERMINALUSE_BASE_URL env var,
        or https://api.terminaluse.com if not set.

    token : str, optional
        Bearer token for user authentication. Defaults to TERMINALUSE_API_KEY env var.

    agent_api_key : str, optional
        API key for agent authentication. Defaults to TERMINALUSE_AGENT_API_KEY env var.

    headers : dict, optional
        Additional headers to send with every request.

    timeout : float, optional
        Request timeout in seconds. Defaults to 60.

    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to True.

    httpx_client : httpx.AsyncClient, optional
        Custom httpx client for making requests.

    auto_refresh_token : bool, optional
        Enable automatic token refresh on expiration. When enabled, the client
        will attempt to refresh expired tokens using stored credentials.
        Defaults to True.

    Examples
    --------
    >>> from terminaluse import AsyncTerminalUse
    >>> client = AsyncTerminalUse()  # Uses env vars
    >>> client = AsyncTerminalUse(token="my-token")  # User auth
    >>> client = AsyncTerminalUse(agent_api_key="my-key")  # Agent auth
    """

    def __init__(
        self,
        *,
        base_url: typing.Optional[str] = None,
        token: typing.Optional[typing.Union[str, typing.Callable[[], str]]] = None,
        agent_api_key: typing.Optional[str] = None,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        timeout: typing.Optional[float] = None,
        follow_redirects: typing.Optional[bool] = True,
        httpx_client: typing.Optional[httpx.AsyncClient] = None,
        auto_refresh_token: bool = True,
    ):
        # Handle base_url from env var
        if base_url is None:
            base_url = os.getenv("TERMINALUSE_BASE_URL", DEFAULT_BASE_URL)

        # Handle auth - read from env vars if not provided
        if token is None:
            token = os.getenv("TERMINALUSE_API_KEY")
        if agent_api_key is None:
            agent_api_key = os.getenv("TERMINALUSE_AGENT_API_KEY")

        # If auto_refresh_token is enabled and token is a string, wrap it in auto-refresh logic
        final_token: typing.Union[str, typing.Callable[[], str]]
        if auto_refresh_token and isinstance(token, str):
            final_token = _create_auto_refresh_token_getter(token)
        elif token:
            final_token = token
        else:
            final_token = ""

        # Fern requires both to be non-None, so use empty string as fallback
        # The backend handles missing auth headers gracefully
        super().__init__(
            base_url=base_url,
            token=final_token,
            agent_api_key=agent_api_key if agent_api_key else "",
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            httpx_client=httpx_client,
        )
