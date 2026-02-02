"""
Tasks CLI commands for creating, listing, and interacting with tasks.

Usage:
    tu tasks create [--filesystem-id <fs_id>] [--message "Hello"]
    tu tasks ls                          # List all tasks
    tu tasks ls <task_id>                # Get task details
    tu tasks ls --status RUNNING         # List running tasks only
    tu tasks send <task_id> --message "Hi"  # Send message to existing task
"""

from __future__ import annotations

import sys
from typing import Any

import questionary
import typer
from rich import print_json
from rich.console import Console

from terminaluse.lib.cli.handlers.cleanup_handlers import cleanup_agent_workflows
from terminaluse.lib.cli.handlers.task_handlers import (
    build_text_content,
    parse_json_event,
    parse_json_params,
    read_message_input,
    resolve_agent_context,
    stream_task_response,
)
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.cli.utils.git_utils import detect_git_info
from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)
console = Console()


# Create Typer app - no callback with positional args to avoid conflicts with subcommands
tasks = typer.Typer(help="Get, list, and delete tasks")


@tasks.command("send")
def send_message(
    task_id: str = typer.Argument(..., help="Task ID to send message to"),
    message: str = typer.Option(None, "--message", "-m", help="Text message to send"),
    event: str = typer.Option(None, "--event", "-e", help="Raw JSON event to send"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name (namespace/name)"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full tool arguments and responses"),
    debug: bool = typer.Option(False, "--debug", hidden=True, help="Print raw stream data"),
):
    """Send a message or event to an existing task."""
    # Validate task_id first
    if task_id is None:
        console.print("[red]Error:[/red] Task ID is required")
        raise typer.Exit(1)

    # Validate mutual exclusivity
    if message and event:
        console.print("[red]Error:[/red] Cannot specify both --message and --event")
        raise typer.Exit(1)

    if not message and not event:
        console.print("[red]Error:[/red] Must specify either --message or --event")
        raise typer.Exit(1)

    _send_to_existing_task(task_id, message, event, agent, config, verbose, debug)


def _send_to_existing_task(
    task_id: str,
    message: str | None,
    event: str | None,
    agent_flag: str | None,
    config_flag: str | None,
    verbose: bool = False,
    debug: bool = False,
) -> None:
    """Send a message or event to an existing task."""
    client = get_authenticated_client()

    # First, retrieve the task to get its full info for streaming
    try:
        task_response = client.tasks.retrieve(task_id=task_id)
        # Extract the Task from TaskResponse if needed
        task = task_response if hasattr(task_response, "id") else task_response
    except Exception as e:
        console.print(f"[red]Error retrieving task {task_id}:[/red] {e}")
        raise typer.Exit(1) from None

    if message:
        # Read message (support stdin)
        resolved_message = read_message_input(message)
        if not resolved_message:
            console.print("[red]Error:[/red] Empty message")
            raise typer.Exit(1)

        content = build_text_content(resolved_message)

        console.print(f"[blue]Sending message to task {task_id}...[/blue]")

        try:
            # Send message as event (async agents use event/send)
            client.tasks.send_event(task_id=task_id, content=content)

            # Stream responses from the agent
            stream_task_response(client, task, timeout=600, debug=debug, verbose=verbose)

            console.print("[green]Message sent.[/green]")
            console.print(f'[dim]Send follow-up: tu tasks send {task_id} -m "your message"[/dim]')

        except Exception as e:
            console.print(f"[red]Error sending message:[/red] {e}")
            console.print(f"Task ID: {task_id}")
            raise typer.Exit(1) from None

    elif event:
        # Parse and send raw JSON event
        event_data = parse_json_event(event)

        console.print(f"[blue]Sending event to task {task_id}...[/blue]")

        try:
            # Build content from event data if it has the expected structure
            if "content" in event_data:
                content = event_data["content"]
            else:
                # Treat the entire event as the content
                content = build_text_content(str(event_data))

            client.tasks.send_event(task_id=task_id, content=content)
            console.print("[green]Event sent successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error sending event:[/red] {e}")
            console.print(f"Task ID: {task_id}")
            raise typer.Exit(1) from None


@tasks.command("create")
def create(
    filesystem_id: str = typer.Option(None, "--filesystem-id", "-f", help="Optional filesystem ID to attach"),
    project_id: str = typer.Option(None, "--project", "-p", help="Project ID for auto-creating filesystem"),
    message: str = typer.Option(None, "--message", "-m", help="Text message (mutually exclusive with --event)"),
    event: str = typer.Option(None, "--event", "-e", help="Raw JSON event (mutually exclusive with --message)"),
    params: str = typer.Option(None, "--params", help="JSON string with task params"),
    params_file: str = typer.Option(None, "--params-file", help="Path to JSON file with task params"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name (namespace/name)"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    name: str = typer.Option(None, "--name", "-n", help="Optional task name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full tool arguments and responses"),
    debug: bool = typer.Option(False, "--debug", hidden=True, help="Print raw stream data"),
):
    """
    Create a new task.

    Examples:
        tu tasks create --message "Hello"
        tu tasks create --filesystem-id <fs_id> --message "Hello"
        tu tasks create --project <proj_id> --message "Hello"
        tu tasks create --params '{"key": "value"}'
        echo "Hello from pipe" | tu tasks create --message -
    """
    # Validate mutual exclusivity
    if message and event:
        console.print("[red]Error:[/red] Cannot specify both --message and --event")
        raise typer.Exit(1)

    client = get_authenticated_client()

    # Resolve agent context
    try:
        agent_context = resolve_agent_context(client, agent, config)
    except Exception as e:
        console.print(f"[red]Error resolving agent:[/red] {e}")
        raise typer.Exit(1) from None

    # Parse params
    task_params = parse_json_params(params, params_file)

    # Detect git branch for version routing
    git_info = detect_git_info()
    git_branch = git_info.branch if git_info.is_git_repo else None

    # Create task
    console.print(f"[blue]Creating task for agent {agent_context.namespace_slug}/{agent_context.short_name}...[/blue]")
    if git_branch:
        console.print(f"[dim]  Branch: {git_branch}[/dim]")

    try:
        task = client.tasks.create(
            agent_name=f"{agent_context.namespace_slug}/{agent_context.short_name}",
            filesystem_id=filesystem_id,
            project_id=project_id,
            name=name,
            params=task_params,
            branch=git_branch,
        )
    except Exception as e:
        console.print(f"[red]Error creating task:[/red] {e}")
        raise typer.Exit(1) from None

    console.print(f"[green]Task created:[/green] {task.id}")

    # If message or event provided, send it
    if message:
        # Read message (support stdin)
        resolved_message = read_message_input(message)
        if not resolved_message:
            console.print("[yellow]Warning:[/yellow] Empty message, skipping")
        else:
            content = build_text_content(resolved_message)

            console.print("[blue]Sending message...[/blue]")

            try:
                # Send message as event (async agents use event/send)
                client.tasks.send_event(task.id, content=content)

                # Stream responses from the agent
                stream_task_response(client, task, timeout=600, debug=debug, verbose=verbose)

                console.print("[green]Message sent.[/green]")
                console.print(f'[dim]Send follow-up: tu tasks send {task.id} -m "your message"[/dim]')

            except Exception as e:
                console.print(f"[red]Error sending message:[/red] {e}")
                console.print("[yellow]Task was created but message failed.[/yellow]")
                console.print(f"Task ID: {task.id}")
                console.print(f"Recovery: tu tasks send {task.id} --message '<your message>'")
                raise typer.Exit(1) from None

    elif event:
        # Parse and send raw JSON event
        event_data = parse_json_event(event)

        console.print("[blue]Sending event...[/blue]")

        try:
            # Build content from event data if it has the expected structure
            if "content" in event_data:
                content = event_data["content"]
            else:
                # Treat the entire event as the content
                content = build_text_content(str(event_data))

            client.tasks.send_event(task.id, content=content)
            console.print("[green]Event sent successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error sending event:[/red] {e}")
            console.print("[yellow]Task was created but event failed.[/yellow]")
            console.print(f"Task ID: {task.id}")
            raise typer.Exit(1) from None
    else:
        # No message/event, just print task info
        print_json(data=task.dict(), default=str)


@tasks.command("ls")
def ls(
    task_id: str = typer.Argument(None, help="Task ID to retrieve (if provided, shows task details)"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name (namespace/name)"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    status: str = typer.Option(None, "--status", "-s", help="Filter by status (e.g., RUNNING, COMPLETED, FAILED)"),
    full: bool = typer.Option(False, "--full", "-F", help="Show full UUIDs"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    List all tasks or get a specific task's details.

    Examples:
        tu tasks ls                          # List all tasks
        tu tasks ls <task_id>                # Get specific task details
        tu tasks ls --agent namespace/agent-name
        tu tasks ls --status RUNNING
    """
    from rich.table import Table

    client = get_authenticated_client()

    # If task_id is provided, get that specific task
    if task_id:
        logger.info(f"Getting task: {task_id}")
        task = client.tasks.retrieve(task_id=task_id)
        print_json(data=task.dict(), default=str)
        return

    # Get agent name from flag or manifest (only if explicitly provided)
    agent_name = None
    if agent or config:
        try:
            from terminaluse.lib.cli.utils.cli_utils import get_agent_name

            agent_name = get_agent_name(agent, config)
        except Exception:
            # No manifest and no agent flag - list all tasks
            pass

    # List tasks
    if agent_name:
        all_tasks = client.tasks.list(agent_name=agent_name)
    else:
        all_tasks = client.tasks.list()

    # Filter by status if specified
    if status:
        status_upper = status.upper()
        filtered_tasks = [
            task
            for task in all_tasks
            if hasattr(task, "status") and task.status and task.status.upper() == status_upper
        ]
    else:
        filtered_tasks = list(all_tasks)

    if not filtered_tasks:
        if status:
            console.print(f"[yellow]No tasks found with status '{status}'[/yellow]")
        elif agent_name:
            console.print(f"[yellow]No tasks found for agent '{agent_name}'[/yellow]")
        else:
            console.print("[yellow]No tasks found[/yellow]")
        return

    # JSON output mode
    if json_output:
        serializable_tasks: list[dict[str, Any]] = []
        for task in filtered_tasks:
            try:
                if hasattr(task, "model_dump"):
                    serializable_tasks.append(task.model_dump(mode="json"))
                else:
                    serializable_tasks.append(
                        {
                            "id": getattr(task, "id", "unknown"),
                            "status": getattr(task, "status", "unknown"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to serialize task: {e}")
                serializable_tasks.append(
                    {
                        "id": getattr(task, "id", "unknown"),
                        "status": getattr(task, "status", "unknown"),
                    }
                )
        print_json(data=serializable_tasks, default=str)
        return

    # Table output mode
    table = Table(title=f"Tasks ({len(filtered_tasks)} total)")
    table.add_column("TASK ID", style="cyan")
    table.add_column("NAME")
    table.add_column("STATUS")
    table.add_column("VERSION", style="dim")

    for task in filtered_tasks:
        # Format task ID
        tid = getattr(task, "id", "unknown")
        display_id = tid if full else (tid[:8] if len(tid) > 8 else tid)

        # Format name
        task_name = getattr(task, "name", None) or "-"

        # Format status with color
        task_status = getattr(task, "status", None) or "-"
        if task_status.upper() == "RUNNING":
            task_status = "[green]running[/green]"
        elif task_status.upper() == "COMPLETED":
            task_status = "[dim]completed[/dim]"
        elif task_status.upper() == "FAILED":
            task_status = "[red]failed[/red]"
        else:
            task_status = task_status.lower()

        # Format version ID
        version_id = getattr(task, "current_version_id", None)
        if version_id:
            display_version = version_id if full else version_id[:8]
        else:
            display_version = "-"

        table.add_row(display_id, task_name, task_status, display_version)

    console.print(table)


@tasks.command()
def delete(
    task_id: str = typer.Argument(..., help="ID of the task to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Delete the task with the given ID.
    """
    is_interactive = sys.stdin.isatty()

    # Confirm deletion
    if not yes:
        if not is_interactive:
            console.print("[red]Error:[/red] Cannot confirm deletion in non-interactive mode.")
            console.print("Use '--yes' or '-y' to skip confirmation prompts.")
            raise typer.Exit(1)
        confirm = questionary.confirm(
            f"Are you sure you want to delete task '{task_id}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    logger.info(f"Deleting task: {task_id}")
    client = get_authenticated_client()
    client.tasks.delete(task_id=task_id)
    console.print(f"[green]✓[/green] Task '{task_id}' deleted")


@tasks.command()
def cleanup(
    agent_name: str = typer.Option(..., help="Name of the agent to cleanup tasks for (namespace/agent-name format)"),
    force: bool = typer.Option(
        False, help="Force cleanup using direct Temporal termination (bypasses development check)"
    ),
):
    """
    Clean up all running tasks/workflows for an agent.

    By default, uses graceful cancellation via agent RPC.
    With --force, directly terminates workflows via Temporal client.
    """
    try:
        console.print(f"[blue]Starting cleanup for agent '{agent_name}'...[/blue]")

        cleanup_agent_workflows(agent_name=agent_name, force=force, development_only=True)

        console.print(f"[green]✓ Cleanup completed for agent '{agent_name}'[/green]")

    except Exception as e:
        console.print(f"[red]Cleanup failed: {str(e)}[/red]")
        logger.exception("Task cleanup failed")
        raise typer.Exit(1) from e


@tasks.command("migrate")
def migrate(
    from_version: str | None = typer.Option(
        None, "--from", "-f", help="Source version ID (migrates all running tasks from this version)"
    ),
    task_ids: str | None = typer.Option(None, "--ids", "-i", help="Comma-separated task IDs to migrate"),
    to_version: str = typer.Option(..., "--to", "-t", help="Target version ID or 'latest'"),
    full: bool = typer.Option(False, "--full", "-F", help="Show full UUIDs"),
):
    """
    Migrate tasks between versions within the same branch.

    Supports two modes:
    - Bulk migration: Use --from to migrate all running tasks from a source version
    - Specific tasks: Use --ids to migrate specific task IDs

    The target can be an explicit version ID or 'latest' to migrate to the active version.

    Examples:
        tu tasks migrate --from ver_abc123 --to ver_def456
        tu tasks migrate --from ver_abc123 --to latest
        tu tasks migrate --ids task_a,task_b,task_c --to ver_def456
        tu tasks migrate --ids task_a --to latest
    """
    from rich.table import Table

    # Validate mutual exclusivity
    if from_version and task_ids:
        console.print("[red]Error:[/red] Cannot specify both --from and --ids")
        console.print("  Use --from to migrate all tasks from a version, OR --ids for specific tasks")
        raise typer.Exit(1)

    if not from_version and not task_ids:
        console.print("[red]Error:[/red] Must specify either --from or --ids")
        console.print("  Use --from <version_id> to migrate all running tasks from a version")
        console.print("  Use --ids <task1,task2,...> to migrate specific tasks")
        raise typer.Exit(1)

    client = get_authenticated_client()

    # Determine if target is 'latest' or a specific version
    to_latest = to_version.lower() == "latest"
    to_version_id = None if to_latest else to_version

    # Parse task IDs if provided
    task_id_list = None
    if task_ids:
        task_id_list = [tid.strip() for tid in task_ids.split(",") if tid.strip()]
        if not task_id_list:
            console.print("[red]Error:[/red] No valid task IDs provided")
            raise typer.Exit(1)

    try:
        # Call the migrate API
        # Build kwargs dynamically to avoid passing None for optional params
        migrate_kwargs: dict[str, Any] = {}
        if from_version:
            migrate_kwargs["from_version_id"] = from_version
        if task_id_list:
            migrate_kwargs["task_ids"] = task_id_list
        if to_latest:
            migrate_kwargs["to_latest"] = True
        if to_version_id:
            migrate_kwargs["to_version_id"] = to_version_id

        response = client.tasks.migrate(**migrate_kwargs)

        # Display results in a table
        migrated_tasks = response.tasks
        if not migrated_tasks:
            console.print("[yellow]No tasks were migrated[/yellow]")
            return

        table = Table(title=f"Migrated {len(migrated_tasks)} task(s)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")

        for task in migrated_tasks:
            # Format ID with optional truncation
            task_id = task.id if full else (task.id if len(task.id) <= 8 else task.id[:8])
            task_name = getattr(task, "name", None) or "-"
            task_status = getattr(task, "status", None) or "-"
            table.add_row(task_id, task_name, task_status)

        console.print(table)

        # Show target version with git hash
        ver = response.to_version
        ver_display = ver.id if full else ver.id[:8]
        git_hash = ver.git_hash[:7] if ver.git_hash else None
        if git_hash:
            console.print(f"\n[green]Target version:[/green] {ver_display} ({git_hash})")
        else:
            console.print(f"\n[green]Target version:[/green] {ver_display}")

    except Exception as e:
        console.print(f"[red]Migration failed:[/red] {e}")
        raise typer.Exit(1) from None


# Add 'list' as a hidden alias for 'ls'
tasks.command("list", hidden=True)(ls)
