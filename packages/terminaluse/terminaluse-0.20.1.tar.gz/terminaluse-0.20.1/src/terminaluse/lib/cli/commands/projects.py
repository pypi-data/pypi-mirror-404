"""
Projects CLI commands for managing projects.

Commands:
- ls: List projects (optionally filtered by namespace)
- get: Get project details
- create: Create a new project
- update: Update a project
- delete: Delete a project
"""

from __future__ import annotations

import sys

import questionary
import typer
from rich.console import Console

console = Console()
projects = typer.Typer(no_args_is_help=True)


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger

    return make_logger(__name__)


@projects.command("ls")
def ls(
    namespace: str | None = typer.Option(
        None,
        "--namespace",
        "-ns",
        help="Filter by namespace slug",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        "-l",
        help="Max results",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List all projects, optionally filtered by namespace."""
    import json

    from terminaluse.lib.cli.utils.client import get_authenticated_client
    from terminaluse.lib.cli.handlers.project_handlers import (
        ProjectError,
        format_projects_table,
        resolve_namespace_id_from_slug,
    )

    logger = _get_logger()

    try:
        client = get_authenticated_client()

        # Resolve namespace slug to ID if provided
        namespace_id = None
        if namespace:
            namespace_id = resolve_namespace_id_from_slug(client, namespace)

        # Build kwargs for API call
        kwargs: dict[str, str | int] = {}
        if namespace_id:
            kwargs["namespace_id"] = namespace_id
        if limit:
            kwargs["limit"] = limit

        # Get projects
        project_list = list(client.projects.list(**kwargs))

        if json_output:
            output = [p.dict() if hasattr(p, "dict") else {"id": p.id, "name": p.name} for p in project_list]
            typer.echo(json.dumps(output, default=str))
            return

        # Format and display
        output = format_projects_table(project_list, namespace)
        console.print(output)

    except ProjectError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project list failed", exc_info=True)
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project list failed", exc_info=True)
        raise typer.Exit(1) from e


@projects.command("get")
def get(
    project_id: str = typer.Argument(..., help="Project ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Get project details."""
    import json

    from terminaluse.lib.cli.utils.client import get_authenticated_client
    from terminaluse.lib.cli.handlers.project_handlers import format_project_summary

    logger = _get_logger()

    try:
        client = get_authenticated_client()
        project = client.projects.retrieve(project_id)

        if json_output:
            output = project.dict() if hasattr(project, "dict") else {"id": project.id}
            typer.echo(json.dumps(output, default=str))
            return

        output = format_project_summary(project)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project get failed", exc_info=True)
        raise typer.Exit(1) from e


@projects.command("create")
def create(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Project name",
    ),
    namespace: str = typer.Option(
        ...,
        "--namespace",
        "-ns",
        help="Namespace slug",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="Project description",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Create a new project."""
    import json

    from terminaluse.lib.cli.utils.client import get_authenticated_client
    from terminaluse.lib.cli.handlers.project_handlers import (
        ProjectError,
        resolve_namespace_id_from_slug,
    )

    logger = _get_logger()

    try:
        client = get_authenticated_client()

        # Resolve namespace slug to ID
        namespace_id = resolve_namespace_id_from_slug(client, namespace)

        # Build kwargs for API call
        kwargs = {
            "name": name,
            "namespace_id": namespace_id,
        }
        if description:
            kwargs["description"] = description

        # Create project
        project = client.projects.create(**kwargs)

        if json_output:
            output = project.dict() if hasattr(project, "dict") else {"id": project.id, "name": project.name}
            typer.echo(json.dumps(output, default=str))
            return

        console.print(f"[green]✓[/green] Created project: {project.id}")
        console.print(f"Name: {project.name}")

    except ProjectError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project create failed", exc_info=True)
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project create failed", exc_info=True)
        raise typer.Exit(1) from e


@projects.command("update")
def update(
    project_id: str = typer.Argument(..., help="Project ID"),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="New project name",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="New project description",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Update a project's name or description."""
    import json

    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    # Validate at least one field is provided
    if name is None and description is None:
        console.print("[red]Error:[/red] Must specify at least --name or --description")
        raise typer.Exit(1)

    try:
        client = get_authenticated_client()

        # Build kwargs for API call (only include provided fields)
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description

        # Update project
        project = client.projects.update(project_id, **kwargs)

        if json_output:
            output = project.dict() if hasattr(project, "dict") else {"id": project.id, "name": project.name}
            typer.echo(json.dumps(output, default=str))
            return

        console.print(f"[green]✓[/green] Updated project: {project.id}")
        console.print(f"Name: {project.name}")
        if project.description:
            console.print(f"Description: {project.description}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project update failed", exc_info=True)
        raise typer.Exit(1) from e


@projects.command("delete")
def delete(
    project_id: str = typer.Argument(..., help="Project ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a project (must be empty)."""
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
            f"Are you sure you want to delete project '{project_id}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        client = get_authenticated_client()
        client.projects.delete(project_id)
        console.print(f"[green]✓[/green] Project '{project_id}' deleted")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Project delete failed", exc_info=True)
        raise typer.Exit(1) from e


# Add 'list' as a hidden alias for 'ls'
projects.command("list", hidden=True)(ls)
