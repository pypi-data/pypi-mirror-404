"""
Task CLI handlers for creating and managing tasks.

This module provides core task-related logic for the CLI.
"""

from __future__ import annotations

import sys
import json
from typing import Any

import typer
from rich.console import Console

from terminaluse import TerminalUse
from terminaluse.types import TaskMessage, TaskResponse, TaskMessageContent_Text
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.cli_utils import get_agent_name, parse_agent_name
from terminaluse.lib.cli.utils.git_utils import detect_git_info

logger = make_logger(__name__)
console = Console()


class AgentContext:
    """Container for resolved agent context information."""

    def __init__(self, short_name: str, namespace_slug: str, namespace_id: str):
        self.short_name = short_name
        self.namespace_slug = namespace_slug
        self.namespace_id = namespace_id


def resolve_agent_context(
    client: TerminalUse,
    agent_flag: str | None = None,
    manifest_flag: str | None = None,
) -> AgentContext:
    """
    Resolve agent context from flag or config.

    Resolution order:
    1. If agent_flag provided, use it directly (mutually exclusive with config_flag)
    2. If config_flag provided, read agent name from that config file (mutually exclusive with agent_flag)
    3. Otherwise, look for config.yaml in current directory

    Args:
        client: The TerminalUse client instance
        agent_flag: Optional agent name in "namespace/name" format
        manifest_flag: Optional path to manifest file

    Returns:
        AgentContext with resolved short_name, namespace_slug, and namespace_id

    Raises:
        typer.Exit: If agent cannot be resolved, or if both flags are provided
    """
    try:
        # Use get_agent_name which handles mutual exclusivity and resolution
        agent_name = get_agent_name(agent_flag, manifest_flag)

        # Parse into components
        namespace_slug, short_name = parse_agent_name(agent_name)

        # Fetch agent to get namespace_id
        agent = client.agents.retrieve_by_name(namespace_slug, short_name)

        return AgentContext(
            short_name=short_name,
            namespace_slug=namespace_slug,
            namespace_id=agent.namespace_id,
        )
    except Exception as e:
        logger.error(f"Failed to resolve agent context: {e}")
        raise


def build_text_content(message: str, author: str = "user") -> TaskMessageContent_Text:
    """
    Build text content for messages.

    Args:
        message: The text content
        author: The message author (default "user")

    Returns:
        TaskMessageContent_Text with author and content fields
    """
    return TaskMessageContent_Text(
        author=author,  # type: ignore[arg-type]
        content=message,
    )


def read_message_input(message_arg: str | None) -> str | None:
    """
    Read message from stdin if '-' or if stdin is piped.

    Logic:
    - If message_arg == "-": read from stdin
    - If message_arg is None AND not sys.stdin.isatty(): read from stdin (pipe detected)
    - Otherwise: return message_arg as-is

    Args:
        message_arg: The message argument from CLI

    Returns:
        The resolved message string, or None if no message
    """
    # Explicit stdin read
    if message_arg == "-":
        return sys.stdin.read().strip()

    # Piped stdin detection (isatty returns True when interactive, False when piped)
    if message_arg is None and not sys.stdin.isatty():
        return sys.stdin.read().strip()

    return message_arg


def stream_task_response(
    client: TerminalUse,
    task: TaskResponse,
    timeout: int = 600,
    debug: bool = False,
    verbose: bool = False,
) -> list[TaskMessage]:
    """
    Stream task responses with character-level streaming.

    This provides real-time streaming output:
    - Text: Printed character-by-character as deltas arrive
    - Tool requests: Buffered until JSON is complete, then displayed
    - Tool responses: Buffered until complete, then displayed
    - Reasoning: Printed dim/italic as deltas arrive

    Args:
        client: The TerminalUse client instance
        task: The task to stream responses for
        timeout: Timeout in seconds (default 600 = 10 minutes)
        debug: If True, print raw SSE events for debugging
        verbose: If True, show full tool arguments and responses without truncation

    Returns:
        Empty list (display-only function, kept for backwards compat)
    """
    from terminaluse.lib.utils.dev_tools.async_messages import stream_task_events

    try:
        stream_task_events(client=client, task=task, timeout=timeout, debug=debug, verbose=verbose)
        return []  # Empty list for backwards compat
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        console.print(f"Resume with: tu tasks {task.id} --message '<your message>'")
        raise typer.Exit(130) from None
    except Exception as e:
        if "timeout" in str(e).lower():
            console.print("[yellow]Stream timed out[/yellow]")
        else:
            console.print(f"[red]Stream error:[/red] {e}")
        console.print(f"Recovery hint: tu tasks {task.id} --message '<resume>'")
        return []


def parse_json_params(
    params_str: str | None = None,
    params_file: str | None = None,
) -> dict[str, Any] | None:
    """
    Parse task parameters from JSON string or file.

    Args:
        params_str: JSON string with params
        params_file: Path to JSON file with params

    Returns:
        Parsed params dict, or None if neither provided

    Raises:
        typer.Exit: If JSON parsing fails or mutual exclusivity violated
    """
    if params_str and params_file:
        console.print("[red]Error:[/red] Cannot specify both --params and --params-file")
        raise typer.Exit(1)

    if params_str:
        try:
            return json.loads(params_str)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in --params:[/red] {e}")
            console.print(f"Input: {params_str[:100]}...")
            raise typer.Exit(1) from None

    if params_file:
        try:
            with open(params_file) as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Params file not found: {params_file}")
            raise typer.Exit(1) from None
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in params file:[/red] {e}")
            raise typer.Exit(1) from None

    return None


def parse_json_event(event_str: str) -> dict[str, Any]:
    """
    Parse raw JSON event.

    Args:
        event_str: JSON string with event data

    Returns:
        Parsed event dict

    Raises:
        typer.Exit: If JSON parsing fails
    """
    try:
        return json.loads(event_str)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in --event:[/red] {e}")
        console.print(f"Input: {event_str[:100]}...")
        raise typer.Exit(1) from None
