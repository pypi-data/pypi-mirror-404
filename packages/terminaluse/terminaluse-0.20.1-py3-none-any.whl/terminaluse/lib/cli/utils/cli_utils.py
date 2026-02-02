from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

import typer
from rich.console import Console

console = Console()


def is_interactive() -> bool:
    """Check if stdin is connected to a terminal (interactive mode).

    Returns:
        True if running interactively (stdin is a TTY), False otherwise.
    """
    return sys.stdin.isatty()


def require_interactive_or_flag(flag_value: bool, flag_name: str = "--yes", prompt_description: str | None = None) -> None:
    """Require either interactive mode or a confirmation flag.

    Use this before questionary prompts to gracefully handle non-interactive environments.

    Args:
        flag_value: The value of the confirmation flag (e.g., --yes)
        flag_name: The name of the flag for the error message
        prompt_description: Description of what the prompt was asking (e.g., "confirm deployment with uncommitted changes")

    Raises:
        typer.Exit: If not interactive and flag is not set
    """
    if not flag_value and not is_interactive():
        if prompt_description:
            console.print(f"[red]Error:[/red] Cannot {prompt_description} in non-interactive mode.")
        else:
            console.print("[red]Error:[/red] Running in non-interactive mode.")
        console.print(f"Use '{flag_name}' or '-y' to skip confirmation prompts.")
        raise typer.Exit(1)


def handle_questionary_cancellation(result: str | None, operation: str = "operation") -> str:
    """Handle questionary cancellation by checking for None and exiting gracefully"""
    if result is None:
        console.print(f"[yellow]{operation.capitalize()} cancelled by user[/yellow]")
        raise typer.Exit(0)
    return result


def get_agent_name(agent: str | None = None, config: str | None = None) -> str:
    """
    Resolve agent name from --agent flag, --config flag, or default config.yaml.

    Resolution order:
    1. From --agent flag if provided (mutually exclusive with --config)
    2. From --config flag if provided (mutually exclusive with --agent)
    3. From config.yaml in current directory if neither flag provided
    4. Error if none available

    Args:
        agent: Optional agent name in 'namespace/agent-name' format
        config: Optional path to config file

    Returns:
        Agent name in 'namespace/agent-name' format

    Raises:
        typer.Exit: If both --agent and --config are provided, or if neither
                    is provided and no config.yaml exists in current directory
    """
    # Enforce mutual exclusivity
    if agent and config:
        console.print("[red]Error:[/red] --agent and --config are mutually exclusive")
        raise typer.Exit(1)

    if agent:
        return agent

    # Determine config path: custom or default
    if config:
        config_path = Path(config)
        if not config_path.exists():
            console.print(f"[red]Error:[/red] Config file not found: {config}")
            raise typer.Exit(1)
    else:
        config_path = Path("config.yaml")

    try:
        from terminaluse.lib.sdk.config.agent_manifest import AgentManifest

        if not config_path.exists():
            raise FileNotFoundError("config.yaml not found")

        config_obj = AgentManifest.from_yaml(str(config_path))
        return config_obj.agent.name  # Returns "namespace/agent-name"
    except FileNotFoundError:
        console.print("[red]Error:[/red] No config.yaml found and --agent not specified")
        raise typer.Exit(1) from None


def parse_agent_name(agent_name: str | None) -> tuple[str, str]:
    """
    Parse 'namespace/agent-name' into (namespace_slug, short_name).

    Args:
        agent_name: Full agent name in 'namespace/agent-name' format

    Returns:
        Tuple of (namespace_slug, agent_short_name)

    Raises:
        typer.Exit: If agent_name is None or not in the correct format
    """
    if agent_name is None:
        console.print("[red]Error:[/red] Agent name is required")
        raise typer.Exit(1)
    if "/" not in agent_name:
        console.print(f"[red]Error:[/red] Agent name must be 'namespace/agent-name', got '{agent_name}'")
        raise typer.Exit(1)
    parts = agent_name.split("/", 1)
    if not parts[0] or not parts[1]:
        console.print("[red]Error:[/red] Both namespace and agent name are required in 'namespace/agent-name' format")
        raise typer.Exit(1)
    return parts[0], parts[1]


def format_relative_time(dt: datetime | None) -> str:
    """Format a datetime as a human-readable relative time string."""
    if dt is None:
        return "-"

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")


def format_git_hash(git_hash: str, is_dirty: bool = False, length: int = 7) -> str:
    """Format a git hash with optional dirty indicator.

    Args:
        git_hash: The full git commit hash
        is_dirty: Whether the working directory had uncommitted changes
        length: Number of characters to show (default: 7)

    Returns:
        Formatted string like "d abc1234" where "d " prefix indicates dirty
    """
    prefix = "d " if is_dirty else ""
    return f"{prefix}{git_hash[:length]}"


def format_version_id(version_id: str, length: int = 8) -> str:
    """Format a version ID to a standard display length.

    Args:
        version_id: The full version ID
        length: Number of characters to show (default: 8)

    Returns:
        Truncated version ID
    """
    return version_id[:length]


def format_git_info(git_hash: str, git_message: str | None, is_dirty: bool = False, max_msg_len: int = 30) -> str:
    """Format git hash and truncated message for display.

    Args:
        git_hash: The git commit hash
        git_message: The commit message (optional)
        is_dirty: Whether the working directory had uncommitted changes
        max_msg_len: Maximum length for the commit message

    Returns:
        Formatted string like "d abc1234 (message)" where "d " prefix indicates dirty
    """
    info = format_git_hash(git_hash, is_dirty)
    if git_message:
        msg = git_message.split("\n")[0][:max_msg_len]
        if len(git_message) > max_msg_len:
            msg += "..."
        info += f" ({msg})"
    return info


def is_tty() -> bool:
    """Check if stdout is connected to a terminal.

    Returns:
        True if stdout is a TTY (human user), False otherwise (piped/scripted).
    """
    return sys.stdout.isatty()


def parse_relative_time(time_str: str) -> datetime:
    """Parse a relative or absolute time string to datetime.

    Supports:
    - Relative: "30s", "5m", "1h", "2d", "1w" (seconds, minutes, hours, days, weeks ago)
    - ISO 8601: "2025-01-29T14:00:00Z" or "2025-01-29"

    Args:
        time_str: Time string in relative or ISO format

    Returns:
        datetime in UTC

    Raises:
        ValueError: If the format is invalid
    """
    import re

    # Try relative format first (e.g., "1h", "30m", "2d")
    match = re.match(r"^(\d+)([smhdw])$", time_str.lower())
    if match:
        from datetime import timedelta

        amount = int(match.group(1))
        unit = match.group(2)

        units = {
            "s": timedelta(seconds=amount),
            "m": timedelta(minutes=amount),
            "h": timedelta(hours=amount),
            "d": timedelta(days=amount),
            "w": timedelta(weeks=amount),
        }

        now = datetime.now(timezone.utc)
        return now - units[unit]

    # Try ISO 8601 format
    try:
        # Handle "Z" suffix and various ISO formats
        normalized = time_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    # Try date-only format (e.g., "2025-01-29")
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    raise ValueError(
        f"Invalid time format: '{time_str}'. "
        f"Use relative (1h, 30m, 2d) or ISO 8601 (2025-01-29T14:00:00Z)."
    )


def format_status(status: str) -> str:
    """Format status with consistent lowercase and coloring.

    Provides centralized status formatting for consistent display across all CLI commands.

    Args:
        status: The status string (case-insensitive)

    Returns:
        Rich-formatted status string with appropriate color
    """
    status_upper = status.upper()
    if status_upper == "ACTIVE":
        return "[green]active[/green]"
    elif status_upper == "READY":
        return "[green]ready[/green]"
    elif status_upper == "DEPLOYING":
        return "[yellow]deploying[/yellow]"
    elif status_upper == "DRAINING":
        return "[yellow]draining[/yellow]"
    elif status_upper == "FAILED":
        return "[red]failed[/red]"
    elif status_upper == "UNHEALTHY":
        return "[red]unhealthy[/red]"
    elif status_upper in ("RETIRED", "ROLLED_BACK"):
        return f"[dim]{status.lower()}[/dim]"
    return status.lower()
