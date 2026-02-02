"""Log sender for shipping agent logs to Nucleus.

The SDK acts as a dumb pipe: all stdout/stderr lines are forwarded raw with
sequence numbers. The backend handles JSON detection, multiline coalescing,
timestamp/level parsing, and origin tagging.
"""

from __future__ import annotations

import asyncio
import calendar
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar
from urllib.parse import urlparse

import httpx
from ulid import ULID

from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)

SDK_VERSION = "2.0.0"


# =============================================================================
# Timezone Awareness Helpers
# =============================================================================


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware and in UTC.

    Args:
        dt: A datetime object, either naive or timezone-aware.

    Returns:
        A timezone-aware datetime in UTC.

    Warnings:
        Emits UserWarning if a naive datetime is encountered.
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's already UTC but warn
        logger.warning("Naive datetime encountered, assuming UTC. Use timezone-aware datetimes for accuracy.")
        return dt.replace(tzinfo=timezone.utc)
    # Convert to UTC if in different timezone
    return dt.astimezone(timezone.utc)


def _parse_iso_timestamp_to_dt(iso_str: str) -> datetime:
    """Parse ISO timestamp ensuring UTC timezone.

    Handles various ISO format variations:
    - Z suffix: "2026-01-27T09:18:49.330Z"
    - Timezone offset: "2026-01-27T09:18:49.330+00:00"
    - Naive (no timezone): "2026-01-27T09:18:49.330"

    Args:
        iso_str: ISO format timestamp string.

    Returns:
        A timezone-aware datetime in UTC.

    Raises:
        ValueError: If the string cannot be parsed as ISO format.
    """
    # Handle 'Z' suffix (UTC indicator)
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1] + "+00:00"

    dt = datetime.fromisoformat(iso_str)

    if dt.tzinfo is None:
        # No timezone specified - assume UTC (with warning)
        return _ensure_utc(dt)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)


# =============================================================================
# OTLP Severity Mapping
# =============================================================================

_SEVERITY_NUMBER = {
    "DEBUG": 5,
    "INFO": 9,
    "WARNING": 13,
    "ERROR": 17,
    "CRITICAL": 21,
}


# =============================================================================
# OTLP Helpers
# =============================================================================


def _iso_to_nano(iso_timestamp: str) -> str:
    """Convert ISO timestamp string to nanoseconds since epoch as string.

    Uses integer arithmetic to avoid floating-point precision loss.
    Ensures all timestamps are interpreted as UTC.

    Args:
        iso_timestamp: ISO format timestamp (e.g., "2026-01-27T09:18:49.330000+00:00")

    Returns:
        Nanoseconds since epoch as string (e.g., "1706454627000000000")
    """
    try:
        # Parse and ensure UTC timezone
        dt = _parse_iso_timestamp_to_dt(iso_timestamp)

        # Use pure integer arithmetic to avoid float precision issues
        # calendar.timegm uses integer arithmetic internally (no float conversion)
        seconds = calendar.timegm(dt.utctimetuple())

        # Get microseconds from the datetime (0-999999)
        microseconds = dt.microsecond

        # Convert to nanoseconds using integer math:
        # seconds * 1_000_000_000 + microseconds * 1_000
        nanos = seconds * 1_000_000_000 + microseconds * 1_000

        return str(nanos)
    except (ValueError, AttributeError, OverflowError, OSError):
        # Fallback to current time if parsing fails
        # Note: We catch multiple exception types because:
        # - ValueError: Invalid ISO format string
        # - AttributeError: None or invalid datetime object
        # - OverflowError: Extreme dates that can't be represented as timestamps
        # - OSError: Timezone conversion failures on some platforms
        now = datetime.now(timezone.utc)
        seconds = calendar.timegm(now.utctimetuple())
        microseconds = now.microsecond
        nanos = seconds * 1_000_000_000 + microseconds * 1_000
        return str(nanos)


# =============================================================================
# OTLP Conversion
# =============================================================================


def _logs_to_otlp(logs: list[dict], task_id: str | None, method: str) -> dict[str, Any]:
    """Convert internal log entries to OTLP resourceLogs format.

    All logs are sent under a single scope.name="raw" for backend processing.

    Args:
        logs: List of log dicts from _build_log_entries
        task_id: Task ID for resource attributes
        method: RPC method for resource attributes

    Returns:
        OTLP-formatted dict with resourceLogs structure
    """
    if not logs:
        return {"resourceLogs": []}

    # Build resource attributes
    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": "agent-sdk"}},
        {"key": "terminaluse.sdk.version", "value": {"stringValue": SDK_VERSION}},
    ]
    if task_id:
        resource_attrs.append({"key": "agent.task_id", "value": {"stringValue": task_id}})
    if method:
        resource_attrs.append({"key": "agent.method", "value": {"stringValue": method}})

    # Build log records — all under single "raw" scope
    log_records = []
    for log in logs:
        level = log.get("level", "INFO")
        attributes = [
            {"key": "log.source", "value": {"stringValue": log.get("source", "unknown")}},
            {"key": "log.id", "value": {"stringValue": log.get("log_id", "")}},
            {"key": "log.seq", "value": {"intValue": str(log.get("seq", 0))}},
        ]

        record: dict[str, Any] = {
            "timeUnixNano": _iso_to_nano(log.get("timestamp", "")),
            "severityNumber": _SEVERITY_NUMBER.get(level, 9),
            "severityText": level,
            "body": {"stringValue": log.get("message", "")},
            "attributes": attributes,
        }

        # Add trace context if available
        trace_id = log.get("trace_id")
        span_id = log.get("span_id")
        if trace_id:
            record["traceId"] = trace_id.zfill(32)[:32]
        if span_id:
            record["spanId"] = span_id.zfill(16)[:16]

        log_records.append(record)

    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": resource_attrs,
                },
                "scopeLogs": [
                    {
                        "scope": {
                            "name": "raw",
                            "version": "",
                        },
                        "logRecords": log_records,
                    }
                ],
            }
        ]
    }


from opentelemetry import trace as otel_trace


class LogSource(str, Enum):
    """Source of the log entry."""

    STDOUT = "stdout"
    STDERR = "stderr"
    SERVER = "server"


class LogLevel(str, Enum):
    """Log level for entries."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _is_development_url(url: str) -> bool:
    """Check if URL is a recognized development/internal endpoint.

    Uses proper URL parsing to validate the hostname, preventing bypass attacks
    via query strings, fragments, or path manipulation.

    Allowed non-HTTPS hosts:
    - localhost / 127.0.0.1 / ::1 (local development)
    - host.docker.internal (Docker Desktop accessing host from containers)
    - *.svc.cluster.local (Kubernetes internal services)

    Args:
        url: The URL to check.

    Returns:
        True if the URL is a recognized development/internal endpoint.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        # Local development (IPv4 and IPv6)
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return True

        # Docker Desktop host access (macOS/Windows)
        if hostname == "host.docker.internal":
            return True

        # Kubernetes internal services
        if hostname.endswith(".svc.cluster.local"):
            return True

        return False
    except Exception:
        return False


class LogSender:
    """
    Sends agent logs to Nucleus for ingestion into ClickHouse.

    This class captures stdout/stderr from sandbox execution and ships them
    to the Nucleus /logs/otlp endpoint in OTLP format. All lines are sent
    raw — the backend handles JSON detection, multiline coalescing,
    timestamp/level parsing, and origin tagging.
    """

    # Class-level cached client with lock for thread safety
    _client: ClassVar[httpx.AsyncClient | None] = None
    _client_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(
        self,
        nucleus_url: str,
        agent_api_key: str | None,
    ):
        """
        Initialize the log sender.

        Args:
            nucleus_url: Base URL for Nucleus API (e.g., "https://api.terminaluse.com")
            agent_api_key: API key for agent authentication

        Raises:
            ValueError: If nucleus_url doesn't use HTTPS (except localhost for development)
        """
        # Enforce HTTPS to protect API keys in transit
        # Allow exceptions for recognized development/internal endpoints
        # (see _is_development_url for the full list)
        if not nucleus_url.startswith("https://") and not _is_development_url(nucleus_url):
            raise ValueError(
                "nucleus_url must use HTTPS to protect API keys. "
                "Allowed non-HTTPS: localhost, host.docker.internal, or *.svc.cluster.local"
            )
        self.nucleus_url = nucleus_url.rstrip("/")
        self.agent_api_key = agent_api_key

    @classmethod
    async def _get_client(cls) -> httpx.AsyncClient:
        """Get or create the shared HTTP client.

        Uses a lock to prevent race conditions during client initialization.
        """
        if cls._client is not None:
            return cls._client

        async with cls._client_lock:
            # Double-check after acquiring lock
            if cls._client is None:
                cls._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=10.0,
                        read=30.0,
                        write=30.0,
                        pool=10.0,
                    ),
                )
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        """Close the shared HTTP client."""
        if cls._client:
            await cls._client.aclose()
            cls._client = None

    def is_configured(self) -> bool:
        """Check if the log sender is properly configured."""
        return bool(self.agent_api_key)

    def _get_otel_context(self) -> tuple[str | None, str | None]:
        """Extract trace_id and span_id from current OTEL context.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None)
            if no active span exists.
        """
        try:
            span = otel_trace.get_current_span()
            if span is not None and span.is_recording():
                ctx = span.get_span_context()
                if ctx is not None and ctx.is_valid:
                    # Format as lowercase hex strings
                    # trace_id is 128-bit (32 hex chars), span_id is 64-bit (16 hex chars)
                    trace_id = format(ctx.trace_id, "032x")
                    span_id = format(ctx.span_id, "016x")
                    return trace_id, span_id
        except Exception as e:
            # Don't let OTEL errors break logging
            logger.debug(f"Failed to get OTEL context: {e}")

        return None, None

    async def send_logs(
        self,
        method: str,
        stdout: str,
        stderr: str,
        task_id: str | None = None,
    ) -> None:
        """
        Send captured stdout/stderr to Nucleus.

        Args:
            method: The RPC method that was called
            stdout: Captured stdout from sandbox execution
            stderr: Captured stderr from sandbox execution
            task_id: Optional task ID for correlation
        """
        if not self.is_configured():
            logger.debug("Log sender not configured, skipping log ingestion")
            return

        logs = self._build_log_entries(method, stdout, stderr, task_id)
        if not logs:
            return

        await self._send_to_nucleus(logs, task_id=task_id, method=method)

    def _build_log_entries(
        self,
        method: str,
        stdout: str,
        stderr: str,
        task_id: str | None,
    ) -> list[dict]:
        """Build log entries from stdout/stderr.

        All lines are forwarded raw with sequence numbers.
        The backend handles JSON detection, multiline coalescing,
        timestamp/level parsing, and origin tagging.
        """
        entries: list[dict] = []
        batch_timestamp = datetime.now(timezone.utc).isoformat()
        trace_id, span_id = self._get_otel_context()
        seq = 0

        for source, text, default_level in [
            (LogSource.STDOUT.value, stdout, LogLevel.INFO.value),
            (LogSource.STDERR.value, stderr, LogLevel.WARNING.value),
        ]:
            for line in text.splitlines():
                if not line.strip():
                    continue

                entries.append(
                    {
                        "log_id": str(ULID()),
                        "timestamp": batch_timestamp,
                        "task_id": task_id,
                        "method": method,
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "source": source,
                        "level": default_level,
                        "message": line,
                        "seq": seq,
                    }
                )
                seq += 1

        return entries

    async def _send_to_nucleus(
        self,
        logs: list[dict],
        task_id: str | None,
        method: str,
    ) -> None:
        """Send logs to Nucleus API in OTLP resourceLogs format."""
        client = await self._get_client()
        url = f"{self.nucleus_url}/logs/otlp"

        # Convert to OTLP format
        otlp_payload = _logs_to_otlp(logs, task_id=task_id, method=method)

        try:
            response = await client.post(
                url,
                json=otlp_payload,
                headers={
                    "x-agent-api-key": self.agent_api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            logger.debug(f"Sent {len(logs)} log entries to Nucleus (OTLP format)")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to send logs to Nucleus: {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout sending logs to Nucleus: {e}")
        except httpx.ConnectError as e:
            logger.warning(f"Connection error sending logs to Nucleus: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error sending logs to Nucleus: {e}")


# Global log sender instance
_log_sender: LogSender | None = None


def get_log_sender() -> LogSender | None:
    """
    Get the global log sender instance.

    Returns None if logging is not configured.
    """
    global _log_sender
    if _log_sender is None:
        from terminaluse.lib.environment_variables import EnvironmentVariables

        env = EnvironmentVariables.refresh()
        if env.TERMINALUSE_BASE_URL and env.TERMINALUSE_AGENT_API_KEY:
            _log_sender = LogSender(
                nucleus_url=env.TERMINALUSE_BASE_URL,
                agent_api_key=env.TERMINALUSE_AGENT_API_KEY,
            )
        else:
            logger.debug("Log sender not configured: missing TERMINALUSE_BASE_URL or TERMINALUSE_AGENT_API_KEY")
    return _log_sender


def reset_log_sender() -> None:
    """Reset the global log sender (primarily for testing)."""
    global _log_sender
    _log_sender = None
