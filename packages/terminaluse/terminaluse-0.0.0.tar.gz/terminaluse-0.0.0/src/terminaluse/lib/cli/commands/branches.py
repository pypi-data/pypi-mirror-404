"""CLI commands for managing branches."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.cli.utils.cli_utils import get_agent_name, parse_agent_name, format_relative_time, format_status

logger = make_logger(__name__)
console = Console()

branches = typer.Typer(no_args_is_help=True)


@branches.command("list")
def list_branches(
    include_retired: bool = typer.Option(False, "--include-retired", help="Include retired branches"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """
    List all branches for the current agent.

    Each branch is an independently deployable instance. By default, retired
    branches are hidden.
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()

    try:
        response = client.agents.branches.list(
            agent_name=agent_short,
            namespace_slug=namespace_slug,
            include_retired=include_retired,
        )

        if not response.branches:
            if include_retired:
                console.print(f"No branches found for agent '{agent_name}'.")
            else:
                console.print(f"No active branches found for agent '{agent_name}'.")
                console.print("\nDeploy with: tu deploy")
            return

        table = Table(title=f"Branches for {agent_name}")
        table.add_column("BRANCH", style="cyan")
        table.add_column("STATUS")
        table.add_column("VERSION")
        table.add_column("REPLICAS", justify="right")
        table.add_column("DEPLOYED")

        for branch in response.branches:
            # Get version info
            version_info = "-"
            if branch.current_version:
                version_info = f"{branch.current_version.git_hash[:7]}"
                if branch.current_version.git_message:
                    msg = branch.current_version.git_message.split("\n")[0][:30]
                    if len(branch.current_version.git_message) > 30:
                        msg += "..."
                    version_info += f" ({msg})"

            # Get deployed time
            deployed_at = "-"
            if branch.current_version:
                deployed_at = format_relative_time(branch.current_version.deployed_at)
            elif branch.updated_at:
                deployed_at = format_relative_time(branch.updated_at)

            # Status comes from current_version if available
            status_str = format_status(branch.current_version.status) if branch.current_version else "[dim]-[/dim]"
            table.add_row(
                branch.git_branch,
                status_str,
                version_info,
                str(branch.replicas),
                deployed_at,
            )

        console.print(table)
        console.print(f"\n{response.total} branch(es)")

        if not include_retired:
            console.print("\n[dim]Use --include-retired to see retired branches.[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to list branches")
        raise typer.Exit(1) from e


@branches.command("show")
def show_branch(
    branch: str = typer.Argument(..., help="Branch name"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Show details for a specific branch."""
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()

    try:
        branch_info = client.agents.branches.retrieve(
            namespace_slug,
            agent_short,
            branch=branch,
        )

        console.print(Panel.fit(f"[bold]Branch: {branch_info.git_branch}[/bold]", border_style="blue"))
        console.print()

        console.print(f"  [cyan]ID:[/cyan]               {branch_info.id}")
        status_str = format_status(branch_info.current_version.status) if branch_info.current_version else "[dim]-[/dim]"
        console.print(f"  [cyan]Status:[/cyan]           {status_str}")
        console.print(f"  [cyan]Branch:[/cyan]           {branch_info.git_branch}")
        console.print(f"  [cyan]Branch (norm):[/cyan]    {branch_info.git_branch_normalized}")
        console.print(f"  [cyan]Replicas:[/cyan]         {branch_info.replicas}")

        acp_url = getattr(branch_info, "acp_url", None)
        if acp_url:
            console.print(f"  [cyan]ACP URL:[/cyan]          {acp_url}")

        console.print()

        if branch_info.current_version:
            console.print("[bold]Current Version[/bold]")
            console.print(f"  [cyan]Version ID:[/cyan]  {branch_info.current_version.id}")
            console.print(f"  [cyan]Git Hash:[/cyan]    {branch_info.current_version.git_hash}")
            console.print(f"  [cyan]Status:[/cyan]      {branch_info.current_version.status}")
            console.print(f"  [cyan]Deployed:[/cyan]    {format_relative_time(branch_info.current_version.deployed_at)}")
            if branch_info.current_version.git_message:
                msg = branch_info.current_version.git_message
                if len(msg) > 100:
                    msg = msg[:97] + "..."
                console.print(f"  [cyan]Message:[/cyan]     {msg}")
            console.print()

        # Timestamps
        if branch_info.created_at:
            console.print(f"  [cyan]Created:[/cyan]  {format_relative_time(branch_info.created_at)}")
        if branch_info.updated_at:
            console.print(f"  [cyan]Updated:[/cyan]  {format_relative_time(branch_info.updated_at)}")

        if branch_info.retired_at:
            console.print()
            console.print("[bold yellow]Retired[/bold yellow]")
            console.print(f"  [cyan]Retired at:[/cyan]  {format_relative_time(branch_info.retired_at)}")
            if branch_info.retired_reason:
                console.print(f"  [cyan]Reason:[/cyan]      {branch_info.retired_reason}")

        console.print()
        console.print("[dim]Commands:[/dim]")
        console.print(f"  [dim]View versions:[/dim] tu versions list --branch {branch}")
        console.print(f"  [dim]View logs:[/dim]     tu agents logs --branch {branch}")

    except Exception as e:
        if "not found" in str(e).lower():
            console.print(f"[red]Error:[/red] Branch '{branch}' not found.")
            console.print("\nThe branch may not have been deployed yet.")
            console.print("Deploy with: tu deploy")
            raise typer.Exit(1) from e
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to get branch")
        raise typer.Exit(1) from e
