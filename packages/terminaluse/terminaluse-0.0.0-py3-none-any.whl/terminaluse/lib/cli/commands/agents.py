from __future__ import annotations

import builtins
import sys
from typing import TYPE_CHECKING

import questionary
import typer
from rich.console import Console

# Lazy imports - these are deferred to function scope for faster CLI startup
if TYPE_CHECKING:
    pass

console = Console()
agents = typer.Typer(no_args_is_help=True)


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger

    return make_logger(__name__)


@agents.command()
def get(
    agent_id: str = typer.Argument(..., help="ID of the agent to get"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    Get the agent with the given ID.
    """
    from rich import print_json
    from rich.panel import Panel

    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()
    logger.info(f"Getting agent with ID: {agent_id}")
    client = get_authenticated_client()
    agent = client.agents.retrieve(agent_id=agent_id)
    logger.info(f"Agent retrieved: {agent}")

    if json_output:
        print_json(data=agent.dict(), default=str)
    else:
        # Display as formatted summary
        agent_name = getattr(agent, "name", agent_id)
        lines = [f"[bold]ID:[/bold] {agent.id}"]
        if hasattr(agent, "name") and agent.name:
            lines.append(f"[bold]Name:[/bold] {agent.name}")
        if hasattr(agent, "description") and agent.description:
            lines.append(f"[bold]Description:[/bold] {agent.description}")
        if hasattr(agent, "namespace_id") and agent.namespace_id:
            lines.append(f"[bold]Namespace ID:[/bold] {agent.namespace_id}")
        if hasattr(agent, "created_at") and agent.created_at:
            lines.append(f"[bold]Created:[/bold] {agent.created_at}")

        panel = Panel("\n".join(lines), title=f"Agent: {agent_name}")
        console.print(panel)


@agents.command("ls")
def ls(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    List all agents.
    """
    from rich import print_json
    from rich.table import Table

    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()
    logger.info("Listing all agents")
    client = get_authenticated_client()
    agents_list = list(client.agents.list())
    logger.info(f"Agents retrieved: {agents_list}")

    if json_output:
        print_json(data=[agent.dict() for agent in agents_list], default=str)
    else:
        if not agents_list:
            console.print("[yellow]No agents found[/yellow]")
            return

        table = Table(title=f"Agents ({len(agents_list)} total)")
        table.add_column("ID", style="dim")
        table.add_column("NAME", style="cyan")
        table.add_column("DESCRIPTION")

        for agent in agents_list:
            agent_id = getattr(agent, "id", "-")
            display_id = agent_id[:12] + "..." if len(agent_id) > 12 else agent_id
            agent_name = getattr(agent, "name", "-") or "-"
            description = getattr(agent, "description", None) or "-"
            # Truncate description if too long
            if len(description) > 50:
                description = description[:47] + "..."
            table.add_row(display_id, agent_name, description)

        console.print(table)


# Add 'list' as a hidden alias for 'ls'
agents.command("list", hidden=True)(ls)


@agents.command()
def delete(
    agent_name: str = typer.Argument(..., help="Name of the agent to delete (namespace/agent-name format)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Delete the agent with the given name.
    """
    from terminaluse.lib.cli.utils.cli_utils import parse_agent_name
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()
    is_interactive = sys.stdin.isatty()

    # Confirm deletion
    if not yes:
        if not is_interactive:
            console.print("[red]Error:[/red] Cannot confirm deletion in non-interactive mode.")
            console.print("Use '--yes' or '-y' to skip confirmation prompts.")
            raise typer.Exit(1)
        confirm = questionary.confirm(
            f"Are you sure you want to delete agent '{agent_name}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    logger.info(f"Deleting agent with name: {agent_name}")
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()
    client.agents.delete_by_name(namespace_slug=namespace_slug, agent_name=agent_short)
    console.print(f"[green]✓[/green] Agent '{agent_name}' deleted")
    logger.info(f"Agent deleted: {agent_name}")


@agents.command()
def cleanup_workflows(
    agent_name: str = typer.Argument(
        ..., help="Name of the agent to cleanup workflows for (namespace/agent-name format)"
    ),
    force: bool = typer.Option(
        False, help="Force cleanup using direct Temporal termination (bypasses development check)"
    ),
):
    """
    Clean up all running workflows for an agent.

    By default, uses graceful cancellation via agent RPC.
    With --force, directly terminates workflows via Temporal client.
    This is a convenience command that does the same thing as 'tu tasks cleanup'.
    """
    from terminaluse.lib.cli.handlers.cleanup_handlers import cleanup_agent_workflows

    logger = _get_logger()
    try:
        console.print(f"[blue]Cleaning up workflows for agent '{agent_name}'...[/blue]")

        cleanup_agent_workflows(agent_name=agent_name, force=force, development_only=True)

        console.print(f"[green]✓ Workflow cleanup completed for agent '{agent_name}'[/green]")

    except Exception as e:
        console.print(f"[red]Cleanup failed: {str(e)}[/red]")
        logger.exception("Agent workflow cleanup failed")
        raise typer.Exit(1) from e


@agents.command(hidden=True)
def build(
    config: str = typer.Option(..., "--config", "-c", help="Path to the config file"),
    registry: str | None = typer.Option(None, help="Registry URL for pushing the built image"),
    repository_name: str | None = typer.Option(None, help="Repository name to use for the built image"),
    platforms: str | None = typer.Option(
        None, help="Platform to build the image for. Please enter a comma separated list of platforms."
    ),
    push: bool = typer.Option(False, help="Whether to push the image to the registry"),
    secret: str | None = typer.Option(
        None,
        help="Docker build secret in the format 'id=secret-id,src=path-to-secret-file'",
    ),
    tag: str | None = typer.Option(None, help="Image tag to use (defaults to 'latest')"),
    build_arg: builtins.list[str] | None = typer.Option(  # noqa: B008
        None,
        help="Docker build argument in the format 'KEY=VALUE' (can be used multiple times)",
    ),
):
    """
    Build an agent image locally from the given manifest.
    """
    from terminaluse.lib.cli.handlers.agent_handlers import build_agent

    logger = _get_logger()
    typer.echo(f"Building agent image from config: {config}")

    # Validate required parameters for building
    if push and not registry:
        typer.echo("Error: --registry is required when --push is enabled", err=True)
        raise typer.Exit(1)

    # Only proceed with build if we have a registry (for now, to match existing behavior)
    if not registry:
        typer.echo("No registry provided, skipping image build")
        return

    platform_list = platforms.split(",") if platforms else ["linux/amd64"]

    try:
        image_url = build_agent(
            config_path=config,
            registry_url=registry,
            repository_name=repository_name,
            platforms=platform_list,
            push=push,
            secret=secret or "",  # Provide default empty string
            tag=tag or "latest",  # Provide default
            build_args=build_arg or [],  # Provide default empty list
        )
        if image_url:
            typer.echo(f"Successfully built image: {image_url}")
        else:
            typer.echo("Image build completed but no URL returned")
    except Exception as e:
        typer.echo(f"Error building agent image: {str(e)}", err=True)
        logger.exception("Error building agent image")
        raise typer.Exit(1) from e


@agents.command(hidden=True)
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to the config file"),
    cleanup_on_start: bool = typer.Option(False, help="Clean up existing workflows for this agent before starting"),
    # Debug options
    debug: bool = typer.Option(False, help="Enable debug mode for both worker and ACP (disables auto-reload)"),
    debug_worker: bool = typer.Option(False, help="Enable debug mode for temporal worker only"),
    debug_acp: bool = typer.Option(False, help="Enable debug mode for ACP server only"),
    debug_port: int = typer.Option(5678, help="Port for remote debugging (worker uses this, ACP uses port+1)"),
    wait_for_debugger: bool = typer.Option(False, help="Wait for debugger to attach before starting"),
) -> None:
    """
    Run an agent locally from the given manifest.
    """
    from terminaluse.lib.cli.debug import DebugConfig, DebugMode
    from terminaluse.lib.cli.handlers.agent_handlers import run_agent
    from terminaluse.lib.cli.handlers.cleanup_handlers import cleanup_agent_workflows
    from terminaluse.lib.sdk.config.agent_manifest import AgentManifest

    logger = _get_logger()
    typer.echo(f"Running agent from config: {config}")

    # Optionally cleanup existing workflows before starting
    if cleanup_on_start:
        try:
            # Parse config to get agent name
            config_obj = AgentManifest.from_yaml(file_path=config)
            agent_name = config_obj.agent.name

            console.print(f"[yellow]Cleaning up existing workflows for agent '{agent_name}'...[/yellow]")
            cleanup_agent_workflows(agent_name=agent_name, force=False, development_only=True)
            console.print("[green]✓ Pre-run cleanup completed[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠ Pre-run cleanup failed: {str(e)}[/yellow]")
            logger.warning(f"Pre-run cleanup failed: {e}")

    # Create debug configuration based on CLI flags
    debug_config = None
    if debug or debug_worker or debug_acp:
        # Determine debug mode
        if debug:
            mode = DebugMode.BOTH
        elif debug_worker and debug_acp:
            mode = DebugMode.BOTH
        elif debug_worker:
            mode = DebugMode.WORKER
        elif debug_acp:
            mode = DebugMode.ACP
        else:
            mode = DebugMode.NONE

        debug_config = DebugConfig(
            enabled=True,
            mode=mode,
            port=debug_port,
            wait_for_attach=wait_for_debugger,
            auto_port=False,  # Use fixed port to match VS Code launch.json
        )

        console.print(f"[blue]🐛 Debug mode enabled: {mode.value}[/blue]")
        if wait_for_debugger:
            console.print("[yellow]⏳ Processes will wait for debugger attachment[/yellow]")

    try:
        run_agent(config_path=config, debug_config=debug_config)
    except Exception as e:
        typer.echo(f"Error running agent: {str(e)}", err=True)
        logger.exception("Error running agent")
        raise typer.Exit(1) from e
