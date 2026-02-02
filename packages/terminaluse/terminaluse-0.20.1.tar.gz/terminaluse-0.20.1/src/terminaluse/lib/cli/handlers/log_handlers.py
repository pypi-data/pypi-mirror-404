"""Handlers for agent log viewing."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime

import typer
from rich.console import Console

from terminaluse import TerminalUse
from terminaluse.core.api_error import ApiError
from terminaluse.lib.cli.utils.cli_utils import is_tty, parse_relative_time
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.utils.logging import make_logger
from terminaluse.types import (
    LogStreamEvent_Connected,
    LogStreamEvent_Error,
    LogStreamEvent_Log,
)

logger = make_logger(__name__)
console = Console()

# Source labels for display (matching platform UI)
SOURCE_LABELS = {
    "stdout": "out",
    "stderr": "err",
    "server": "sys",
}

# Level colors for TTY output
LEVEL_COLORS = {
    "DEBUG": "dim",
    "INFO": "cyan",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red bold",
}

# Level severity order (for minimum-severity filtering)
LEVEL_SEVERITY = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
}


class LogsError(Exception):
    """Custom exception for logs-related errors with user-friendly messages."""

    pass


# Regex pattern for text-format logs: ISO_TIMESTAMP [LEVEL] message
# Matches: 2026-01-31T04:50:06.724Z [DEBUG] Getting matching hook commands...
_TEXT_LOG_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z?)\s+\[(\w+)\]\s+(.+)$")


def _parse_log_message(message: str) -> dict | None:
    """Try to parse message and extract inner log fields.

    Attempts parsing in order:
    1. JSON format: {"ts": "...", "level": "...", "msg": "..."}
    2. Text format: 2026-01-31T04:50:06.724Z [DEBUG] message

    The SDK wraps raw log lines in an envelope. If the original log was
    structured (JSON or text format), we extract the actual timestamp,
    level, and message from within.

    Args:
        message: The raw message string from the log envelope.

    Returns:
        Dict with extracted fields (ts, level, msg, logger) or None if
        the message couldn't be parsed.
    """
    # Try JSON first
    result = _parse_json_message(message)
    if result:
        return result

    # Try text format: ISO_TIMESTAMP [LEVEL] message
    match = _TEXT_LOG_PATTERN.match(message)
    if match:
        return {
            "ts": match.group(1),
            "level": match.group(2).upper(),
            "msg": match.group(3),
        }

    return None


def _parse_json_message(message: str) -> dict | None:
    """Try to parse message as JSON and extract inner log fields.

    Args:
        message: The raw message string from the log envelope.

    Returns:
        Dict with extracted fields (ts, level, msg, logger) or None if
        the message is not valid JSON or doesn't have expected fields.
    """
    try:
        parsed = json.loads(message)
        if not isinstance(parsed, dict):
            return None

        # Extract fields - support common naming conventions
        result = {}

        # Timestamp: ts, timestamp, time, @timestamp
        ts = parsed.get("ts") or parsed.get("timestamp") or parsed.get("time") or parsed.get("@timestamp")
        if ts:
            result["ts"] = ts

        # Level: level, lvl, severity
        level = parsed.get("level") or parsed.get("lvl") or parsed.get("severity")
        if level:
            # Normalize level to uppercase
            result["level"] = str(level).upper()

        # Message: msg, message, text
        msg = parsed.get("msg") or parsed.get("message") or parsed.get("text")
        if msg:
            result["msg"] = msg

        # Logger: logger, name, source
        logger_name = parsed.get("logger") or parsed.get("name")
        if logger_name:
            result["logger"] = logger_name

        # Only return if we extracted at least a message
        if result.get("msg"):
            return result

        return None
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def fetch_logs(
    agent_name: str,
    task_id: str | None = None,
    level: str | None = None,
    source: str | None = None,
    since: str | None = None,
    until: str | None = None,
    version: str | None = None,
    limit: int = 500,
) -> None:
    """
    Fetch and display logs for an agent.

    In TTY mode (interactive terminal): Pretty-prints logs with colors,
    parsing JSON messages to extract inner timestamp/level/message.

    In non-TTY mode (piped/scripted): Streams JSONL to stdout with
    enriched parsed_* fields for pipeline consumption.

    Args:
        agent_name: Name of the agent (format: namespace/name) or agent ID
        task_id: Filter by task ID
        level: Minimum log level (shows this level and more severe)
        source: Filter by source (stdout, stderr, server)
        since: Start time (relative like "1h" or ISO 8601)
        until: End time (relative like "1h" or ISO 8601)
        version: Filter by agent version ID
        limit: Maximum number of log entries to fetch
    """
    client = get_authenticated_client()
    is_tty_mode = is_tty()

    # Parse time filters
    since_dt: datetime | None = None
    until_dt: datetime | None = None

    try:
        if since:
            since_dt = parse_relative_time(since)
        if until:
            until_dt = parse_relative_time(until)
    except ValueError as e:
        if is_tty_mode:
            console.print(f"[red]Error:[/red] {e}")
        else:
            print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)

    # Fetch logs from API (don't filter by level - we'll do min-severity client-side)
    try:
        logs, has_more = _query_logs(
            client,
            agent_name,
            task_id=task_id,
            source=source,
            since=since_dt,
            until=until_dt,
            branch_id=version,  # version maps to branch_id in API
            limit=limit,
        )
    except LogsError as e:
        if is_tty_mode:
            console.print(f"[red]Error:[/red] {e}")
        else:
            print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        if is_tty_mode:
            console.print(f"[red]Unexpected error:[/red] {e}")
        else:
            print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)

    # Apply minimum-severity level filter client-side
    if level:
        logs = _filter_by_min_level(logs, level)

    # Handle empty results
    if not logs:
        if is_tty_mode:
            console.print(f"[dim]No logs found for agent '{agent_name}'[/dim]")
        # Non-TTY: Output nothing (empty JSONL stream is valid)
        return

    # Output based on mode
    if is_tty_mode:
        _output_tty(logs, has_more=has_more, limit=limit)
    else:
        _output_jsonl(logs, agent_name)


def _get_effective_level(log: dict) -> str:
    """Get the effective log level (parsed inner level or envelope level)."""
    message = log.get("message", "")
    parsed = _parse_log_message(message)
    if parsed and "level" in parsed:
        return parsed["level"]
    return log.get("level", "INFO")


def _filter_by_min_level(logs: list[dict], min_level: str) -> list[dict]:
    """Filter logs to include only those at or above the minimum severity level.

    Args:
        logs: List of log entries.
        min_level: Minimum level (e.g., "WARNING" includes WARNING, ERROR, CRITICAL).

    Returns:
        Filtered list of logs.
    """
    min_severity = LEVEL_SEVERITY.get(min_level, 0)

    filtered = []
    for log in logs:
        effective_level = _get_effective_level(log)
        log_severity = LEVEL_SEVERITY.get(effective_level, 0)
        if log_severity >= min_severity:
            filtered.append(log)

    return filtered


def _query_logs(
    client: TerminalUse,
    agent_name: str,
    limit: int = 500,
    task_id: str | None = None,
    source: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    branch_id: str | None = None,
    after_id: str | None = None,
) -> tuple[list[dict], bool]:
    """Query logs from Nucleus API using SDK.

    Note: Level filtering is done client-side for min-severity semantics.

    Returns:
        Tuple of (logs, has_more) where logs is a list of log dicts
        and has_more indicates if more logs are available.
    """
    try:
        response = client.logs.list(
            agent_name=agent_name,
            task_id=task_id,
            source=source,
            since=since,
            until=until,
            branch_id=branch_id,
            limit=limit,
            after_id=after_id,
        )
        # Convert LogQueryEntry objects to dicts for compatibility
        logs = [log.model_dump() for log in response.logs]
        has_more = getattr(response, "has_more", False)
        return logs, has_more
    except ApiError as e:
        status = e.status_code
        if status == 404:
            raise LogsError(f"Agent '{agent_name}' not found. Use `tu agents list` to see available agents.") from e
        elif status == 422:
            # Validation error - try to extract details from response
            detail = _extract_error_detail(e)
            raise LogsError(f"Invalid request: {detail}") from e
        elif status == 503:
            raise LogsError("Logging service is temporarily unavailable. Please try again in a few moments.") from e
        elif status == 401:
            raise LogsError("Authentication failed. Please run `tu login` to re-authenticate.") from e
        elif status == 403:
            raise LogsError(f"Permission denied. You don't have access to view logs for agent '{agent_name}'.") from e
        else:
            raise LogsError(f"Failed to fetch logs (HTTP {status}). Please try again.") from e
    except Exception as e:
        if "timeout" in str(e).lower():
            raise LogsError("Request timed out. The logging service may be slow. Please try again.") from e
        elif "connect" in str(e).lower() or "network" in str(e).lower():
            raise LogsError("Network error: Unable to connect to the logging service. Check your connection.") from e
        raise


def _extract_error_detail(error: ApiError) -> str:
    """Extract human-readable error detail from API error response."""
    try:
        # Try to get body from the error
        if hasattr(error, "body") and error.body:
            body = error.body
            if isinstance(body, dict):
                # FastAPI validation error format
                if "detail" in body:
                    detail = body["detail"]
                    if isinstance(detail, list):
                        # Pydantic validation errors
                        messages = []
                        for err in detail:
                            loc = ".".join(str(x) for x in err.get("loc", []))
                            msg = err.get("msg", "")
                            messages.append(f"{loc}: {msg}" if loc else msg)
                        return "; ".join(messages)
                    return str(detail)
                if "message" in body:
                    return body["message"]
            return str(body)
    except Exception:
        pass
    return "Invalid parameters. Check your input and try again."


def _enrich_log_entry(log: dict) -> dict:
    """Enrich log entry with parsed inner fields.

    Adds 'parsed_*' fields if the message contains extractable fields
    (JSON or text format). This preserves the original envelope data
    while making the inner fields available.

    Args:
        log: Original log entry dict.

    Returns:
        Enriched log entry with parsed_ts, parsed_level, parsed_msg,
        parsed_logger fields if extraction succeeded.
    """
    message = log.get("message", "")
    parsed = _parse_log_message(message)

    if not parsed:
        return log

    enriched = log.copy()
    if "ts" in parsed:
        enriched["parsed_ts"] = parsed["ts"]
    if "level" in parsed:
        enriched["parsed_level"] = parsed["level"]
    if "msg" in parsed:
        enriched["parsed_msg"] = parsed["msg"]
    if "logger" in parsed:
        enriched["parsed_logger"] = parsed["logger"]

    return enriched


def _get_effective_timestamp(log: dict) -> str:
    """Get the effective timestamp for sorting (parsed or envelope)."""
    message = log.get("message", "")
    parsed = _parse_log_message(message)
    if parsed and "ts" in parsed:
        return parsed["ts"]
    return log.get("timestamp", "")


def _logs_span_multiple_days(logs: list[dict]) -> bool:
    """Check if logs span more than 24 hours."""
    if len(logs) < 2:
        return False

    timestamps = [_get_effective_timestamp(log) for log in logs]
    timestamps = [ts for ts in timestamps if ts]  # Filter empty

    if len(timestamps) < 2:
        return False

    try:
        # Parse first and last timestamps
        first = datetime.fromisoformat(min(timestamps).replace("Z", "+00:00"))
        last = datetime.fromisoformat(max(timestamps).replace("Z", "+00:00"))
        # Check if they span more than 24 hours
        return (last - first).total_seconds() > 86400
    except (ValueError, TypeError):
        return False


def _output_tty(logs: list[dict], has_more: bool = False, limit: int = 500) -> None:
    """Output logs in pretty-printed TTY format."""
    # Sort by effective timestamp (parsed inner ts or envelope timestamp)
    # This ensures chronological order even when some logs have parsed timestamps
    sorted_logs = sorted(logs, key=_get_effective_timestamp)

    # Check if we need to show dates (logs span multiple days)
    show_date = _logs_span_multiple_days(sorted_logs)

    # Display logs in chronological order
    for log in sorted_logs:
        _print_log_line(log, show_date=show_date)

    # Show pagination indicator if more logs available
    if has_more:
        console.print(
            f"\n[dim]Showing {len(logs)} logs (more available). "
            f"Use --limit to fetch more, --since/--until to narrow the range, "
            f"or -f to stream new logs.[/dim]"
        )


def _output_jsonl(logs: list[dict], agent_name: str) -> None:
    """Output logs as JSONL to stdout for pipeline/agent consumption."""
    # Sort by effective timestamp for chronological order
    sorted_logs = sorted(logs, key=_get_effective_timestamp)

    # Stream JSONL to stdout
    for log in sorted_logs:
        # Enrich log with parsed inner fields if available
        enriched = _enrich_log_entry(log)
        json.dump(enriched, sys.stdout, default=str)
        sys.stdout.write("\n")


def _print_log_line(log: dict, show_date: bool = False) -> None:
    """Print a single log line with color formatting.

    If the message contains inner fields (JSON or text format), we display
    those instead of the envelope values for better readability.

    Args:
        log: Log entry dict.
        show_date: If True, include date in timestamp (for multi-day logs).
    """
    # Get envelope values as defaults
    envelope_timestamp = log.get("timestamp", "")
    envelope_level = log.get("level", "INFO")
    source = log.get("source", "stdout")
    raw_message = log.get("message", "")
    envelope_logger = log.get("logger", "")

    # Try to extract inner fields from message (JSON or text format)
    parsed = _parse_log_message(raw_message)

    if parsed:
        # Use inner values, falling back to envelope
        timestamp = parsed.get("ts", envelope_timestamp)
        level = parsed.get("level", envelope_level)
        message = parsed.get("msg", raw_message)
        logger_name = parsed.get("logger", envelope_logger)
    else:
        # Plain text message - use envelope values
        timestamp = envelope_timestamp
        level = envelope_level
        message = raw_message
        logger_name = envelope_logger

    # Format timestamp (with date if logs span multiple days)
    timestamp_str = _format_timestamp(timestamp, include_date=show_date)

    # Format level with color
    level_color = LEVEL_COLORS.get(level, "")
    level_str = f"[{level_color}]{level:<5}[/{level_color}]" if level_color else f"{level:<5}"

    # Format source label
    source_label = SOURCE_LABELS.get(source, source[:3])

    # Format message with optional logger prefix
    # Escape square brackets to prevent Rich from interpreting as style tags
    # Omit "raw" logger as it's not meaningful (just the envelope default)
    if logger_name and logger_name != "raw":
        msg_display = f"[dim]\\[{logger_name}][/dim] {message}"
    else:
        msg_display = message

    # Print formatted line
    console.print(f"[dim][{timestamp_str}][/dim] {level_str} {source_label:<3}  {msg_display}")


def _format_timestamp(timestamp: str, include_date: bool = False) -> str:
    """Format timestamp for display.

    Args:
        timestamp: ISO format timestamp string.
        include_date: If True, include date (Jan 31 04:50:01.123).

    Returns:
        Formatted timestamp string.
    """
    try:
        if isinstance(timestamp, str):
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            # Format time as HH:MM:SS.mmm (3 digits for milliseconds)
            time_str = dt.strftime("%H:%M:%S") + f".{dt.microsecond // 1000:03d}"
            if include_date:
                # Include short date: "Jan 31 04:50:01.123"
                return dt.strftime("%b %d ") + time_str
            return time_str
        else:
            return str(timestamp)
    except Exception:
        return timestamp[:12] if len(timestamp) >= 12 else timestamp


def stream_logs(
    agent_name: str,
    task_id: str | None = None,
    level: str | None = None,
    source: str | None = None,
    version: str | None = None,
) -> None:
    """
    Stream logs for an agent in real-time (like tail -f).

    Connects to SSE stream and prints logs as they arrive.
    Auto-disconnects after 5 minutes for cost control.

    In TTY mode: Pretty-prints with colors (same format as fetch_logs).
    In non-TTY mode: Streams JSONL to stdout for pipeline consumption.

    Args:
        agent_name: Name of the agent (format: namespace/name) or agent ID
        task_id: Filter by task ID
        level: Minimum log level
        source: Filter by source (stdout, stderr, server)
        version: Filter by agent version ID (maps to branch_id)
    """
    client = get_authenticated_client()
    is_tty_mode = is_tty()

    if is_tty_mode:
        console.print(f"[dim]Streaming logs for {agent_name}... (Ctrl+C to stop)[/dim]")

    try:
        # Call SDK stream method - returns iterator of typed SSE events
        for event in client.logs.stream(
            agent_name=agent_name,
            task_id=task_id,
            level=level,
            source=source,
            branch_id=version,  # version maps to branch_id in API
        ):
            if isinstance(event, LogStreamEvent_Connected):
                if is_tty_mode:
                    console.print("[dim]Connected. Waiting for new logs...[/dim]\n")

            elif isinstance(event, LogStreamEvent_Error):
                if is_tty_mode:
                    console.print(f"[red]Stream error:[/red] {event.message}")
                else:
                    print(f"Error: {event.message}", file=sys.stderr)
                # Error event usually means stream is ending
                break

            elif isinstance(event, LogStreamEvent_Log):
                # Convert to dict for helper functions
                log_dict = event.model_dump()
                if is_tty_mode:
                    _print_log_line(log_dict, show_date=False)
                else:
                    # JSONL output for piping
                    enriched = _enrich_log_entry(log_dict)
                    json.dump(enriched, sys.stdout, default=str)
                    sys.stdout.write("\n")
                    sys.stdout.flush()  # Ensure real-time output when piped

            else:
                # Unknown event type - log for debugging but continue
                logger.debug(f"Unknown stream event type: {type(event).__name__}")

    except KeyboardInterrupt:
        if is_tty_mode:
            console.print("\n[dim]Stream stopped.[/dim]")
        raise typer.Exit(0)
    except ApiError as e:
        status = e.status_code
        if status == 404:
            error_msg = f"Agent '{agent_name}' not found. Use `tu agents list` to see available agents."
        elif status == 401:
            error_msg = "Authentication failed. Please run `tu login` to re-authenticate."
        elif status == 403:
            error_msg = f"Permission denied. You don't have access to view logs for agent '{agent_name}'."
        else:
            error_msg = f"Failed to stream logs (HTTP {status}). Please try again."

        if is_tty_mode:
            console.print(f"[red]Error:[/red] {error_msg}")
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        if is_tty_mode:
            console.print(f"[red]Unexpected error:[/red] {e}")
        else:
            print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
