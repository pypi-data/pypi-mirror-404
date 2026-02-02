"""CLI command for viewing agent logs."""

from __future__ import annotations

import typer

# Valid log levels in severity order (least to most severe)
VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def logs(
    agent_name: str = typer.Argument(..., help="Agent name (format: namespace/name) or agent ID"),
    task: str | None = typer.Option(None, "--task", help="Filter by task ID"),
    level: str | None = typer.Option(
        None, "--level", "-l", help="Minimum log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    ),
    source: str | None = typer.Option(None, "--source", help="Filter by source (stdout, stderr, server)"),
    since: str | None = typer.Option(None, "--since", help="Start time (e.g., 1h, 30m, 2d, or ISO 8601)"),
    until: str | None = typer.Option(None, "--until", help="End time (e.g., 1h, 30m, 2d, or ISO 8601)"),
    version: str | None = typer.Option(None, "--version", "-v", help="Filter by agent version ID"),
    limit: int = typer.Option(500, "--limit", "-n", help="Maximum number of logs to fetch"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Stream new logs in real-time (like tail -f)"),
) -> None:
    """
    View logs for an agent.

    Examples:
        tu logs myorg/my-agent
        tu logs myorg/my-agent --since 1h --level WARNING
        tu logs myorg/my-agent --task task_abc123 --source stderr
        tu logs myorg/my-agent -f                          # Stream new logs
        tu logs myorg/my-agent -f --level ERROR            # Stream only errors

    The --level flag uses minimum severity: --level WARNING shows WARNING,
    ERROR, and CRITICAL logs.

    Output modes:
        TTY (terminal):  Colorized, human-readable format
        Non-TTY (piped): Streams JSONL to stdout for pipeline consumption

    Streaming mode (-f):
        Streams only NEW logs after connection (like tail -f).
        Auto-disconnects after 5 minutes for cost control.
        --since, --until, and --limit are ignored in streaming mode.
    """
    from terminaluse.lib.cli.handlers.log_handlers import fetch_logs, stream_logs

    # Validate and normalize level
    normalized_level = None
    if level:
        normalized_level = _normalize_level(level)

    if follow:
        # Streaming mode: --since, --until, --limit don't make sense
        stream_logs(
            agent_name=agent_name,
            task_id=task,
            level=normalized_level,
            source=source,
            version=version,
        )
    else:
        # Batch mode: fetch historical logs
        fetch_logs(
            agent_name=agent_name,
            task_id=task,
            level=normalized_level,
            source=source,
            since=since,
            until=until,
            version=version,
            limit=limit,
        )


def _normalize_level(level: str) -> str:
    """Normalize and validate log level input.

    Handles common variations like WARN -> WARNING, err -> ERROR.

    Args:
        level: User-provided level string.

    Returns:
        Normalized level string (uppercase, full name).

    Raises:
        typer.BadParameter: If level is not recognized.
    """
    normalized = level.upper().strip()

    # Handle common abbreviations
    aliases = {
        "WARN": "WARNING",
        "ERR": "ERROR",
        "CRIT": "CRITICAL",
        "FATAL": "CRITICAL",
    }
    normalized = aliases.get(normalized, normalized)

    if normalized not in VALID_LEVELS:
        raise typer.BadParameter(f"Invalid level '{level}'. " f"Valid levels: {', '.join(VALID_LEVELS)}")

    return normalized
