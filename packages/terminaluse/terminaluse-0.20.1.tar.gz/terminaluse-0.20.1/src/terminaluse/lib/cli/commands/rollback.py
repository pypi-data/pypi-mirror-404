"""CLI command for rolling back environments to previous versions."""

from __future__ import annotations

import typer
import questionary
from rich.table import Table
from rich.console import Console

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.cli.utils.cli_utils import (
    get_agent_name,
    format_git_hash,
    parse_agent_name,
    format_version_id,
    format_relative_time,
    handle_questionary_cancellation,
    require_interactive_or_flag,
)
from terminaluse.lib.cli.utils.git_utils import detect_git_info

logger = make_logger(__name__)
console = Console()


def rollback(
    branch: str | None = typer.Option(None, "--branch", "-b", help="Branch to rollback (defaults to current git branch)"),
    version: str | None = typer.Option(None, "--version", "-v", help="Target version ID (defaults to previous)"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    Rollback a branch to a previous version.

    By default, rolls back to the immediately previous version.
    Use --version to specify a specific version ID.

    If --branch is not specified, the current git branch is used.

    NOTE: Pending secrets (in EnvVar table) are NOT modified by rollback.
    The rollback uses the secrets_snapshot from the target version.
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()

    # JSON mode implies --yes (skip confirmation)
    if json_output:
        yes = True

    # Determine effective branch
    if branch is None:
        git_info = detect_git_info(".")
        effective_branch = git_info.branch or "main"
        if not json_output:
            console.print(f"Using current git branch: '{effective_branch}'")
    else:
        effective_branch = branch
        if not json_output:
            console.print(f"Using specified branch: '{effective_branch}'")

    try:
        # Get recent versions for this branch
        try:
            versions_response = client.agents.versions.list(
                namespace_slug,
                agent_short,
                branch=effective_branch,
                limit=10,
            )
        except Exception as e:
            if "not found" in str(e).lower():
                console.print(f"[red]Error:[/red] Branch '{effective_branch}' not found.")
                console.print("\nThe branch may not have been deployed yet.")
                raise typer.Exit(1) from e
            raise

        if not versions_response.versions:
            console.print(f"[red]Error:[/red] No versions found for branch '{effective_branch}'.")
            console.print("\nDeploy first before attempting rollback.")
            raise typer.Exit(1)

        if len(versions_response.versions) < 2 and version is None:
            console.print(f"[red]Error:[/red] Cannot rollback - only one version exists for branch '{effective_branch}'.")
            console.print("\nNo previous version to rollback to.")
            raise typer.Exit(1)

        # Find the current (ACTIVE) version - it may not be the newest after a rollback
        current_version = next(
            (v for v in versions_response.versions if v.status == "ACTIVE"),
            versions_response.versions[0]  # Fall back to newest if no ACTIVE found
        )
        current_version_index = next(
            (i for i, v in enumerate(versions_response.versions) if v.id == current_version.id),
            0
        )

        # Show recent versions (skip in JSON mode)
        if not json_output:
            console.print(f"\n[bold]Recent versions for branch '{effective_branch}':[/bold]")

            table = Table()
            table.add_column("VERSION ID", style="cyan")
            table.add_column("GIT HASH")
            table.add_column("STATUS")
            table.add_column("DEPLOYED")
            table.add_column("MESSAGE")

            for ver in versions_response.versions[:5]:
                status = ver.status
                if ver.id == current_version.id:
                    status = "[green]current[/green]"

                msg = ver.git_message or ""
                if len(msg) > 40:
                    msg = msg[:37] + "..."

                is_dirty = getattr(ver, "is_dirty", False) or False
                table.add_row(
                    format_version_id(ver.id),
                    format_git_hash(ver.git_hash, is_dirty),
                    status,
                    format_relative_time(ver.deployed_at),
                    msg,
                )

            console.print(table)
            console.print()

        # Determine target version
        target_version_id = version
        target_version = None

        if target_version_id:
            # Find the specified version (supports prefix matching for 8-char short IDs)
            matching_versions = [
                v for v in versions_response.versions if v.id.startswith(target_version_id)
            ]
            if len(matching_versions) == 0:
                console.print(f"[red]Error:[/red] Version '{target_version_id}' not found.")
                console.print("\nUse one of the version IDs shown above.")
                raise typer.Exit(1)
            if len(matching_versions) > 1:
                console.print(f"[red]Error:[/red] Version prefix '{target_version_id}' is ambiguous.")
                console.print("\nMultiple versions match:")
                for v in matching_versions:
                    console.print(f"  - {v.id}")
                console.print("\nProvide more characters to disambiguate.")
                raise typer.Exit(1)
            target_version = matching_versions[0]
            target_version_id = target_version.id  # Use full ID for API call
        else:
            # Default to the version after the current one (older version)
            # This is the sensible default: rollback goes to an older version
            next_index = current_version_index + 1
            if next_index >= len(versions_response.versions):
                console.print("[red]Error:[/red] No previous version to rollback to.")
                console.print("\nThe current version is already the oldest available.")
                raise typer.Exit(1)
            target_version = versions_response.versions[next_index]
            target_version_id = target_version.id

        # Show what will change (skip in JSON mode)
        if not json_output:
            current_is_dirty = getattr(current_version, "is_dirty", False) or False
            target_is_dirty = getattr(target_version, "is_dirty", False) or False
            console.print("[bold]Rollback summary:[/bold]")
            console.print(f"  [cyan]From:[/cyan] {format_version_id(current_version.id)} → [cyan]To:[/cyan] {format_version_id(target_version.id)}")
            console.print(f"  [cyan]Git:[/cyan]  {format_git_hash(current_version.git_hash, current_is_dirty)} → {format_git_hash(target_version.git_hash, target_is_dirty)}")
            if target_version.git_message:
                msg = target_version.git_message.split("\n")[0]
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                console.print(f"  [cyan]Target message:[/cyan] {msg}")
            console.print()
            console.print("[yellow]Note:[/yellow] Pending secrets will NOT be modified.")
            console.print("  The rollback uses the secrets snapshot from the target version.")
            console.print()

        # Confirmation
        if not yes:
            # Ensure we're in interactive mode before prompting
            require_interactive_or_flag(yes, "--yes", f"confirm rollback of branch '{effective_branch}'")
            confirm = questionary.confirm(
                f"Rollback branch '{effective_branch}' to version {format_version_id(target_version.id)}?"
            ).ask()
            if not handle_questionary_cancellation(str(confirm) if confirm else None, "rollback") or not confirm:
                console.print("[yellow]Rollback cancelled.[/yellow]")
                raise typer.Exit(0)

        # Execute rollback
        if not json_output:
            console.print(f"Rolling back branch '{effective_branch}'...")

        response = client.agents.branches.rollback(
            namespace_slug=namespace_slug,
            agent_name=agent_short,
            branch=effective_branch,
            target_version_id=target_version_id,
        )

        if json_output:
            import json
            output = {
                "branch": effective_branch,
                "from_version_id": response.from_version_id,
                "from_git_hash": response.from_git_hash,
                "to_version_id": response.to_version_id,
                "to_git_hash": response.to_git_hash,
                "version_status": response.version_status,
                "message": response.message,
            }
            typer.echo(json.dumps(output, default=str))
        else:
            console.print()
            console.print(f"[green]✓[/green] Rollback initiated for branch '{effective_branch}'")
            console.print(f"  [cyan]From:[/cyan] {format_version_id(response.from_version_id)} ({response.from_git_hash[:7]})")
            console.print(f"  [cyan]To:[/cyan]   {format_version_id(response.to_version_id)} ({response.to_git_hash[:7]})")
            console.print(f"  [cyan]Status:[/cyan] {response.version_status}")
            console.print(f"  [cyan]Message:[/cyan] {response.message}")
            console.print()
            console.print(f"[dim]Check status with: tu branches show {effective_branch}[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to rollback")
        raise typer.Exit(1) from e
