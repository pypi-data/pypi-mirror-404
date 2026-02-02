"""
Filesystem CLI commands for managing filesystems.

Commands:
- create: Create a new filesystem
- ls: List filesystems for a project
- get: Get filesystem details
- push: Upload directory to filesystem
- pull: Download filesystem to local directory
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

console = Console()
filesystems = typer.Typer(no_args_is_help=True)


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger

    return make_logger(__name__)


@filesystems.command("create")
def create(
    project_id: str = typer.Option(
        ...,
        "--project-id",
        "-p",
        help="Project ID (required)",
    ),
    dir: str | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Local directory to push after creation",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Optional filesystem name",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Create a new filesystem, optionally pushing a directory."""
    import json

    from terminaluse.lib.cli.handlers.filesystem_handlers import (
        FilesystemError,
        _format_bytes,
        create_filesystem,
        push_directory,
    )
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    try:
        client = get_authenticated_client()

        # Create the filesystem
        fs = create_filesystem(client, project_id, name)

        if json_output:
            output = fs.dict() if hasattr(fs, "dict") else {"id": fs.id}
            typer.echo(json.dumps(output, default=str))
            return

        console.print(f"[green]✓[/green] Created filesystem: {fs.id}")

        # Optionally push directory
        if dir:
            local_path = Path(dir).resolve()
            console.print(f"Uploading {local_path} to filesystem {fs.id}...")
            files_count, uncompressed_size, compressed_size = push_directory(client, fs.id, local_path)
            console.print(
                f"Done. Uploaded {files_count} files "
                f"({_format_bytes(uncompressed_size)} → {_format_bytes(compressed_size)} compressed)"
            )
        else:
            console.print(f"Push files with: tu fs push {fs.id} <path>")
            console.print(f"Pull files with: tu fs pull {fs.id} <path>")

    except FilesystemError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem create failed", exc_info=True)
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem create failed", exc_info=True)
        raise typer.Exit(1) from e


@filesystems.command("ls")
def ls(
    project_id: str | None = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Project ID (optional, lists all projects if omitted)",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List filesystems. Shows all filesystems across all projects if no project ID specified."""
    import json

    from terminaluse.lib.cli.handlers.filesystem_handlers import (
        format_filesystems_table,
        format_filesystems_table_all_projects,
        list_all_filesystems,
        list_filesystems,
    )
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    try:
        client = get_authenticated_client()

        if project_id:
            # List filesystems for specific project
            filesystems_list = list_filesystems(client, project_id)
        else:
            # List all filesystems across all projects
            filesystems_list, project_map = list_all_filesystems(client)

        if json_output:
            output = [fs.dict() if hasattr(fs, "dict") else {"id": fs.id} for fs in filesystems_list]
            typer.echo(json.dumps(output, default=str))
            return

        if project_id:
            output = format_filesystems_table(filesystems_list, project_id)
        else:
            output = format_filesystems_table_all_projects(filesystems_list, project_map)

        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem list failed", exc_info=True)
        raise typer.Exit(1) from e


@filesystems.command("get")
def get(
    filesystem_id: str = typer.Argument(..., help="Filesystem ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Get filesystem details."""
    import json

    from terminaluse.lib.cli.handlers.filesystem_handlers import (
        format_filesystem_summary,
        get_filesystem,
        get_filesystem_file_count,
    )
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    try:
        client = get_authenticated_client()
        fs = get_filesystem(client, filesystem_id)
        file_count = get_filesystem_file_count(client, filesystem_id)

        if json_output:
            output = fs.dict() if hasattr(fs, "dict") else {"id": fs.id}
            output["file_count"] = file_count
            typer.echo(json.dumps(output, default=str))
            return

        output = format_filesystem_summary(fs, file_count)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem get failed", exc_info=True)
        raise typer.Exit(1) from e


@filesystems.command("push")
def push(
    filesystem_id: str = typer.Argument(..., help="Filesystem ID"),
    local_path: str = typer.Argument(..., help="Local directory path to upload"),
):
    """Push a local directory to the filesystem."""
    from terminaluse.lib.cli.handlers.filesystem_handlers import (
        FilesystemError,
        _format_bytes,
        push_directory,
    )
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    try:
        client = get_authenticated_client()
        path = Path(local_path).resolve()

        console.print(f"Uploading {path} to filesystem {filesystem_id}...")
        files_count, uncompressed_size, compressed_size = push_directory(client, filesystem_id, path)
        console.print(
            f"Done. Uploaded {files_count} files "
            f"({_format_bytes(uncompressed_size)} → {_format_bytes(compressed_size)} compressed)"
        )

    except FilesystemError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem push failed", exc_info=True)
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem push failed", exc_info=True)
        raise typer.Exit(1) from e


@filesystems.command("pull")
def pull(
    filesystem_id: str = typer.Argument(..., help="Filesystem ID"),
    local_path: str = typer.Argument(..., help="Local directory path to download to"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Clear existing directory contents before extracting",
    ),
):
    """Pull filesystem contents to a local directory."""
    from terminaluse.lib.cli.handlers.filesystem_handlers import (
        FilesystemError,
        _format_bytes,
        pull_directory,
    )
    from terminaluse.lib.cli.utils.client import get_authenticated_client

    logger = _get_logger()

    try:
        client = get_authenticated_client()
        path = Path(local_path).resolve()

        console.print(f"Downloading filesystem {filesystem_id} to {path}...")
        files_count, bytes_extracted = pull_directory(client, filesystem_id, path, force)
        console.print(f"Done. Extracted {files_count} files ({_format_bytes(bytes_extracted)})")

    except FilesystemError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.debug("Filesystem pull failed", exc_info=True)
        raise typer.Exit(1) from e
