import warnings
from typing import Optional

# Suppress Pydantic V1 compatibility warning on Python 3.14+
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible with Python 3.14")

import typer

from terminaluse.lib.cli.commands.agents import agents
from terminaluse.lib.cli.commands.auth import login, logout, whoami
from terminaluse.lib.cli.commands.deploy import deploy
from terminaluse.lib.cli.commands.env import env
from terminaluse.lib.cli.commands.filesystem import filesystems
from terminaluse.lib.cli.commands.init import init
from terminaluse.lib.cli.commands.keys import keys
from terminaluse.lib.cli.commands.logs import logs
from terminaluse.lib.cli.commands.ls import ls
from terminaluse.lib.cli.commands.projects import projects
from terminaluse.lib.cli.commands.rollback import rollback
from terminaluse.lib.cli.commands.tasks import tasks
from terminaluse.version import __version__


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"tu {__version__}")
        raise typer.Exit()


# Create the main Typer application
app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 800},
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=True,
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Terminal Use CLI - Deploy and manage AI agents."""
    pass


# Authentication commands
app.command(
    help="Authenticate with the tu platform",
    rich_help_panel="Authentication",
)(login)
app.command(
    help="Log out and clear stored credentials",
    rich_help_panel="Authentication",
)(logout)
app.command(
    help="Show current authentication status",
    rich_help_panel="Authentication",
)(whoami)

# Core workflow commands
app.command(
    help="Initialize a new agent project with a template",
    rich_help_panel="Workflow",
)(init)
app.command(
    help="Deploy an agent to the tu platform",
    rich_help_panel="Workflow",
)(deploy)
app.command(
    help="List recent versions, or events for a branch",
    rich_help_panel="Workflow",
)(ls)
app.command(
    help="Rollback a branch to a previous version",
    rich_help_panel="Workflow",
)(rollback)
app.command(
    help="View logs for an agent",
    rich_help_panel="Workflow",
)(logs)

# Resource management subcommands
app.add_typer(agents, name="agents", help="Manage agents", rich_help_panel="Resources")
app.add_typer(tasks, name="tasks", help="Manage tasks", rich_help_panel="Resources")
app.add_typer(projects, name="projects", help="Manage projects", rich_help_panel="Resources")
app.add_typer(env, name="env", help="Manage environment variables", rich_help_panel="Resources")
app.add_typer(filesystems, name="fs", help="Manage filesystems", rich_help_panel="Resources")
app.add_typer(filesystems, name="filesystems", help="Manage filesystems", hidden=True)  # Alias
app.add_typer(keys, name="keys", help="Manage webhook keys", rich_help_panel="Resources")


if __name__ == "__main__":
    app()
