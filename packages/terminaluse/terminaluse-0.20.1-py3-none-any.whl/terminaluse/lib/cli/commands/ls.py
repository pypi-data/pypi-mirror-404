"""CLI command for listing recent branches or branch events."""

from __future__ import annotations

import time
from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import typer
from rich.table import Table
from rich.console import Console

from terminaluse import TerminalUse
from terminaluse.core import ApiError
from terminaluse.types import BranchResponse
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.cli.utils.cli_utils import (
    get_agent_name,
    format_git_hash,
    format_git_info,
    parse_agent_name,
    format_status,
    format_version_id,
    format_relative_time,
)

logger = make_logger(__name__)
console = Console()


@dataclass
class VersionDisplay:
    """Version data for display."""

    id: str
    git_branch: str
    git_hash: str
    git_message: str | None
    status: str
    deployed_at: datetime
    author_name: str
    is_dirty: bool


@dataclass
class EventDisplay:
    """Event data for display."""

    created_at: datetime
    event_type: str
    version_id: str
    triggered_by: str | None
    actor_email: str | None


def _format_event_type(event_type: str) -> str:
    """Format event type with color."""
    # Remove VERSION_ prefix for cleaner display
    display_type = event_type.replace("VERSION_", "")

    if display_type in ("CREATED", "ACTIVATED"):
        return f"[green]{display_type}[/green]"
    elif display_type == "FAILED":
        return f"[red]{display_type}[/red]"
    elif display_type in ("ROLLED_BACK_FROM", "ROLLED_BACK_TO"):
        return f"[yellow]{display_type}[/yellow]"
    elif display_type in ("DRAINING", "RETIRED"):
        return f"[dim]{display_type}[/dim]"
    elif display_type == "REDEPLOYED":
        return f"[cyan]{display_type}[/cyan]"
    return display_type


def _list_versions(
    client: TerminalUse,
    agent_name: str,
    limit: int,
    include_retired: bool,
    json_output: bool = False,
) -> None:
    """List recent versions across all branches."""
    import json

    start_time = time.time()
    namespace_slug, short_name = parse_agent_name(agent_name)

    # Step 1: Get all branches
    branches_response = client.agents.branches.list(
        namespace_slug=namespace_slug,
        agent_name=short_name,
        include_retired=include_retired,
    )

    if not branches_response.branches:
        if json_output:
            typer.echo(json.dumps([]))
        else:
            console.print(f"No branches found for agent '[bold]{agent_name}[/bold]'.")
            console.print("\nDeploy with: [cyan]tu deploy[/cyan]")
        return

    # Step 2: Fetch versions from each branch in parallel
    all_versions: list[VersionDisplay] = []
    versions_per_branch = max(3, limit // len(branches_response.branches) + 1)

    def fetch_versions(branch: BranchResponse):
        try:
            response = client.branches.versions.list(
                branch_id=branch.id,
                limit=versions_per_branch,
            )
            return [
                VersionDisplay(
                    id=v.id,
                    git_branch=v.git_branch,
                    git_hash=v.git_hash,
                    git_message=v.git_message,
                    status=v.status,
                    deployed_at=v.deployed_at,
                    author_name=v.author_name,
                    is_dirty=v.is_dirty or False,
                )
                for v in response.versions
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch versions for {branch.git_branch}: {e}")
            return []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_versions, branch) for branch in branches_response.branches]
        for future in as_completed(futures):
            all_versions.extend(future.result())

    if not all_versions:
        if json_output:
            typer.echo(json.dumps([]))
        else:
            console.print(f"No versions found for agent '[bold]{agent_name}[/bold]'.")
        return

    # Step 3: Sort by deployed_at and limit
    all_versions.sort(key=lambda v: v.deployed_at, reverse=True)
    display_versions = all_versions[:limit]

    # JSON output mode
    if json_output:
        output = [
            {
                "id": ver.id,
                "git_branch": ver.git_branch,
                "git_hash": ver.git_hash,
                "git_message": ver.git_message,
                "status": ver.status,
                "deployed_at": ver.deployed_at.isoformat() if ver.deployed_at else None,
                "author_name": ver.author_name,
                "is_dirty": ver.is_dirty,
            }
            for ver in display_versions
        ]
        typer.echo(json.dumps(output, default=str))
        return

    # Step 4: Display
    elapsed_ms = int((time.time() - start_time) * 1000)
    console.print(f"> Versions for [bold]{agent_name}[/bold] [{elapsed_ms}ms]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("AGE", style="dim")
    table.add_column("BRANCH", style="cyan")
    table.add_column("VERSION", style="dim")
    table.add_column("STATUS")
    table.add_column("GIT")
    table.add_column("AUTHOR")

    for ver in display_versions:
        table.add_row(
            format_relative_time(ver.deployed_at),
            ver.git_branch,
            format_version_id(ver.id),
            format_status(ver.status),
            format_git_info(ver.git_hash, ver.git_message, ver.is_dirty),
            ver.author_name,
        )

    console.print(table)

    if len(all_versions) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(all_versions)}. Use -n to see more.[/dim]")


def _list_events(
    client: TerminalUse,
    agent_name: str,
    branch: str,
    limit: int,
    json_output: bool = False,
) -> None:
    """List events for a specific branch."""
    import json

    start_time = time.time()
    namespace_slug, short_name = parse_agent_name(agent_name)

    # Step 1: Get the branch
    try:
        branch_info = client.agents.branches.retrieve(
            namespace_slug=namespace_slug,
            agent_name=short_name,
            branch=branch,
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] Branch '{branch}' not found.")
        console.print(f"\nAvailable branches can be seen with: [cyan]tu ls[/cyan]")
        logger.debug(f"Failed to get branch: {e}")
        raise typer.Exit(1) from e

    # Step 2: Fetch events
    try:
        events_response = client.branches.events.list(branch_id=branch_info.id, limit=limit)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch events: {e}")
        raise typer.Exit(1) from e

    if not events_response.events:
        if json_output:
            typer.echo(json.dumps([]))
        else:
            console.print(f"No events found for [bold]{agent_name}[/bold]@{branch}.")
        return

    # Step 3: Build display data and sort chronologically (most recent first)
    events: list[EventDisplay] = []
    for ev in events_response.events:
        events.append(
            EventDisplay(
                created_at=ev.created_at,
                event_type=ev.event_type,
                version_id=ev.version_id,
                triggered_by=ev.content.triggered_by if ev.content else None,
                actor_email=ev.content.actor_email if ev.content else None,
            )
        )
    events.sort(key=lambda e: e.created_at, reverse=True)

    # Step 4: Fetch version details for git hash display
    unique_version_ids = {ev.version_id for ev in events if ev.version_id}
    version_info: dict[str, tuple[str, bool]] = {}  # version_id -> (git_hash, is_dirty)

    def fetch_version(version_id: str) -> tuple[str, str, bool] | None:
        try:
            version = client.versions.retrieve(version_id)
            return (version_id, version.git_hash, version.is_dirty or False)
        except Exception as e:
            logger.debug(f"Failed to fetch version {version_id}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_version, vid) for vid in unique_version_ids]
        for future in as_completed(futures):
            result = future.result()
            if result:
                vid, git_hash, is_dirty = result
                version_info[vid] = (git_hash, is_dirty)

    # JSON output mode
    if json_output:
        output = [
            {
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "event_type": ev.event_type,
                "version_id": ev.version_id,
                "git_hash": version_info.get(ev.version_id, (None, False))[0] if ev.version_id else None,
                "triggered_by": ev.triggered_by,
                "actor_email": ev.actor_email,
            }
            for ev in events
        ]
        typer.echo(json.dumps(output, default=str))
        return

    # Step 5: Display
    elapsed_ms = int((time.time() - start_time) * 1000)
    console.print(f"> Events for [bold]{agent_name}[/bold]@{branch} [{elapsed_ms}ms]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("AGE", style="dim")
    table.add_column("EVENT")
    table.add_column("VERSION", style="dim")
    table.add_column("GIT")
    table.add_column("TRIGGER", style="dim")

    for ev in events:
        git_display = "-"
        if ev.version_id and ev.version_id in version_info:
            git_hash, is_dirty = version_info[ev.version_id]
            git_display = format_git_hash(git_hash, is_dirty)

        table.add_row(
            format_relative_time(ev.created_at),
            _format_event_type(ev.event_type),
            format_version_id(ev.version_id) if ev.version_id else "-",
            git_display,
            ev.triggered_by.lower() if ev.triggered_by else "-",
        )

    console.print(table)

    if events_response.has_more:
        console.print(f"\n[dim]Showing {len(events)} events. Use -n to see more.[/dim]")


def ls(
    branch: Optional[str] = typer.Argument(None, help="Branch name to show events for"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of items to show"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    include_retired: bool = typer.Option(False, "--all", help="Include retired branches (versions mode only)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    List recent branches or events for a branch.

    Without arguments, shows recent versions across all branches.
    With a branch name, shows lifecycle events for that branch.

    Examples:
        tu ls              # List recent versions
        tu ls main         # List events for 'main' branch
        tu ls -n 20        # Show 20 most recent versions
        tu ls --json       # Output as JSON for scripting
    """
    agent_name = get_agent_name(agent, config)
    client = get_authenticated_client()

    try:
        if branch:
            # Show events for specific branch
            _list_events(client, agent_name, branch, limit, json_output)
        else:
            # Show versions across all branches
            _list_versions(client, agent_name, limit, include_retired, json_output)

    except typer.Exit:
        raise
    except ApiError as e:
        # Handle API errors based on status code
        if e.status_code == 404:
            if e.body and isinstance(e.body, dict) and "message" in e.body:
                console.print(f"[red]Error:[/red] {e.body['message']}")
            else:
                console.print(f"[red]Error:[/red] Agent '{agent_name}' not found")
        else:
            if e.body and isinstance(e.body, dict) and "message" in e.body:
                console.print(f"[red]Error:[/red] {e.body['message']}")
            else:
                console.print(f"[red]Error:[/red] {e!s}")
            logger.debug(f"API error: {e!s}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to list branches")
        raise typer.Exit(1) from e
