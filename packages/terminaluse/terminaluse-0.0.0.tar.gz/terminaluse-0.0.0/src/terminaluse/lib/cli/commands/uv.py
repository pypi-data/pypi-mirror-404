from __future__ import annotations

import os
import sys
import subprocess

import typer


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger
    return make_logger(__name__)


uv = typer.Typer(
    help="Wrapper for uv command with TerminalUse-specific enhancements",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)

sync_args = typer.Argument(None, help="Additional arguments to pass to uv sync")


@uv.command()
def sync(
    ctx: typer.Context,
    index: str | None = typer.Option(None, "--index", "-i", help="UV index URL to use for sync"),
    group: str | None = typer.Option(
        None,
        "--group",
        "-g",
        help="Include dependencies from the specified dependency group",
    ),
    args: list[str] = sync_args,
):
    """Sync dependencies with optional UV_INDEX support"""
    args = args or []

    # Check if help was requested
    if "--help" in args or "-h" in args:
        # Show our custom help instead of passing to uv
        typer.echo(ctx.get_help())
        return

    if index:
        os.environ["UV_INDEX_URL"] = index
        _get_logger().info(f"Using provided UV_INDEX_URL: {index}")

    # Build the uv sync command
    cmd = ["uv", "sync"]

    # Add group if specified
    if group:
        cmd.extend(["--group", group])
        _get_logger().info(f"Using dependency group: {group}")

    # Add any additional arguments
    cmd.extend(args)

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        _get_logger().error(f"uv sync failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        _get_logger().error("uv command not found. Please install uv first.")
        sys.exit(1)


add_args = typer.Argument(None, help="Additional arguments to pass to uv add")


@uv.command()
def add(
    ctx: typer.Context,
    index: str | None = typer.Option(None, "--index", "-i", help="UV index URL to use for add"),
    args: list[str] = add_args,
):
    """Add dependencies with optional UV_INDEX support"""

    args = args or []

    # Check if help was requested
    if "--help" in args or "-h" in args:
        # Show our custom help instead of passing to uv
        typer.echo(ctx.get_help())
        return

    if index:
        os.environ["UV_INDEX_URL"] = index
        _get_logger().info(f"Using provided UV_INDEX_URL: {index}")

    # Build the uv add command
    cmd = ["uv", "add"] + (args or [])

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        _get_logger().error(f"uv add failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        _get_logger().error("uv command not found. Please install uv first.")
        sys.exit(1)


run_args = typer.Argument(None, help="Arguments to pass to uv")


@uv.command()
def run(
    ctx: typer.Context,
    args: list[str] = run_args,
):
    """Run any uv command with arguments"""
    if not args:
        # If no arguments provided, show help
        typer.echo(ctx.get_help())
        return

    # Build the uv command
    cmd = ["uv"] + args

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        _get_logger().error(f"uv command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        _get_logger().error("uv command not found. Please install uv first.")
        sys.exit(1)
