"""Local HTTP callback server for OAuth authentication flow.

Implements a temporary local server to receive the OAuth callback
from the browser after user authentication.
"""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlparse


@dataclass
class AuthorizationResult:
    """Result from OAuth authorization callback."""

    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    # Class-level attributes set by CallbackServer
    authorization_result: AuthorizationResult | None = None
    expected_state: str | None = None
    on_callback: Callable[[AuthorizationResult], None] | None = None

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        result = AuthorizationResult(
            code=params.get("code", [None])[0],
            state=params.get("state", [None])[0],
            error=params.get("error", [None])[0],
            error_description=params.get("error_description", [None])[0],
        )

        # Validate state if expected
        if _CallbackHandler.expected_state and result.state != _CallbackHandler.expected_state:
            result = AuthorizationResult(
                error="state_mismatch",
                error_description="State parameter does not match. Possible CSRF attack.",
            )

        _CallbackHandler.authorization_result = result

        # Send response to browser
        self._send_response(result)

        # Notify callback
        if _CallbackHandler.on_callback:
            _CallbackHandler.on_callback(result)

    def _send_response(self, result: AuthorizationResult) -> None:
        """Send a simple text response to the browser."""
        if result.error:
            message = f"Authentication failed: {result.error}"
            if result.error_description:
                message += f" - {result.error_description}"
        else:
            message = "Authentication successful. You can close this window."

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


def find_available_port(start: int = 8400, end: int = 8500) -> int:
    """
    Find an available port in the given range.

    Args:
        start: Start of port range
        end: End of port range

    Returns:
        Available port number

    Raises:
        RuntimeError: If no port is available
    """
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port in range {start}-{end}")


class CallbackServer:
    """
    Local HTTP server to receive OAuth callback.

    This server listens on localhost for the browser redirect after
    user authentication, then extracts the authorization code.

    Usage:
        server = CallbackServer(expected_state="...")
        redirect_uri = server.start()
        # Open browser to authorization URL with redirect_uri
        result = server.wait_for_callback(timeout=120)
        server.stop()
    """

    def __init__(
        self,
        expected_state: str | None = None,
        port: int | None = None,
    ):
        """
        Initialize callback server.

        Args:
            expected_state: Expected state parameter for CSRF validation
            port: Specific port to use (or None for auto-select)
        """
        self.expected_state = expected_state
        self.port = port or find_available_port()
        self.server: HTTPServer | None = None
        self.thread: threading.Thread | None = None
        self._result: AuthorizationResult | None = None
        self._result_ready = threading.Event()

    @property
    def redirect_uri(self) -> str:
        """Get the redirect URI for this server."""
        return f"http://127.0.0.1:{self.port}/callback"

    def start(self) -> str:
        """
        Start the callback server.

        Returns:
            The redirect URI to use in the authorization request
        """
        # Reset class-level state
        _CallbackHandler.expected_state = self.expected_state
        _CallbackHandler.authorization_result = None
        _CallbackHandler.on_callback = self._on_callback

        # Create and start server
        self.server = HTTPServer(("127.0.0.1", self.port), _CallbackHandler)

        # Start in background thread
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

        return self.redirect_uri

    def _serve(self) -> None:
        """Serve requests until shutdown."""
        if self.server:
            self.server.serve_forever()

    def _on_callback(self, result: AuthorizationResult) -> None:
        """Handle callback result."""
        self._result = result
        self._result_ready.set()

    def wait_for_callback(self, timeout: float = 120) -> AuthorizationResult:
        """
        Wait for the OAuth callback.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            Authorization result from callback

        Raises:
            TimeoutError: If callback not received in time
        """
        if not self._result_ready.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for authorization callback")

        # Result is guaranteed to be set by _on_callback before event is signaled
        assert self._result is not None
        return self._result

    def stop(self) -> None:
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

    def __enter__(self) -> "CallbackServer":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
