from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

# Lazy imports for faster CLI startup - heavy deps imported in functions
if TYPE_CHECKING:
    from terminaluse.lib.cli.debug import DebugConfig
    from terminaluse.lib.sdk.config.agent_manifest import AgentManifest

console = Console()


def _print_docker_build_header():
    """Print a styled header for Docker build output."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🐳 Docker Build Output[/bold cyan]",
        border_style="cyan",
    ))


def _print_docker_build_footer(success: bool = True):
    """Print a styled footer for Docker build output."""
    if success:
        console.print(Panel.fit(
            "[bold green]✓ Docker build completed[/bold green]",
            border_style="green",
        ))
    else:
        console.print(Panel.fit(
            "[bold red]✗ Docker build failed[/bold red]",
            border_style="red",
        ))
    console.print()


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger
    return make_logger(__name__)


class DockerBuildError(Exception):
    """An error occurred during docker build"""


def build_agent(
    config_path: str,
    registry_url: str,
    repository_name: str | None,
    platforms: list[str],
    push: bool = False,
    secret: str | None = None,
    tag: str | None = None,
    build_args: list[str] | None = None,
    verbose: bool = False,
) -> str:
    """Build the agent locally and optionally push to registry

    Args:
        config_path: Path to the agent config file
        registry_url: Registry URL for pushing the image
        push: Whether to push the image to the registry
        secret: Docker build secret in format 'id=secret-id,src=path-to-secret-file'
        tag: Image tag to use (defaults to 'latest')
        build_args: List of Docker build arguments in format 'KEY=VALUE'
        verbose: Show docker build output (default: False, quiet mode)

    Returns:
        The image URL
    """
    # Lazy imports - python_on_whales is heavy
    from python_on_whales import DockerException, docker
    from terminaluse.lib.sdk.config.agent_manifest import AgentManifest

    logger = _get_logger()

    agent_manifest = AgentManifest.from_yaml(file_path=config_path)
    build_context_root = (Path(config_path).parent / agent_manifest.build.context.root).resolve()

    repository_name = repository_name or agent_manifest.agent.name

    # Prepare image name
    if registry_url:
        image_name = f"{registry_url}/{repository_name}"
    else:
        image_name = repository_name

    if tag:
        image_name = f"{image_name}:{tag}"
    else:
        image_name = f"{image_name}:latest"

    with agent_manifest.context_manager(build_context_root) as build_context:
        logger.debug(f"Building image {image_name} locally...")

        # Log build context information for debugging
        logger.debug(f"Build context path: {build_context.path}")
        logger.debug(
            f"Dockerfile path: {build_context.path / build_context.dockerfile_path}"  # type: ignore[operator]
        )

        # Prepare required build arguments
        context_path = str(build_context.path)
        dockerfile_path = str(build_context.path / build_context.dockerfile_path)  # type: ignore[operator]
        tags = [image_name]

        # Prepare optional build arguments - use empty dict if not provided
        docker_build_args: dict[str, str] = {}
        if build_args:
            for arg in build_args:
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    docker_build_args[key] = value
                else:
                    logger.warning(f"Invalid build arg format: {arg}. Expected KEY=VALUE")

            if docker_build_args:
                logger.info(f"Using build args: {list(docker_build_args.keys())}")

        # Prepare secrets list if provided - use empty list if not
        secrets_list: list[str] = [secret] if secret else []

        # Create temp file for build logs
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w",
            prefix="tu-docker-build-",
            suffix=".log",
            delete=False,
        ) as tmp:
            log_file = tmp.name

        if verbose:
            _print_docker_build_header()
        else:
            console.print(f"[dim]Build logs: {log_file}[/dim]")
            console.print("[dim]Use --verbose to show build output[/dim]")

        with open(log_file, "w", buffering=1) as f:  # Line buffering for real-time writes
            try:
                # stream_logs=True makes buildx.build return an iterator of log lines
                build_output = docker.buildx.build(
                    context_path=context_path,
                    file=dockerfile_path,
                    tags=tags,
                    platforms=platforms,
                    build_args=docker_build_args,
                    secrets=secrets_list,
                    push=push,
                    stream_logs=True,
                )
                # With stream_logs=True, build() returns Iterator[str]
                assert isinstance(build_output, Iterator), "Expected iterator with stream_logs=True"
                for line in build_output:
                    f.write(line)
                    f.flush()
                    if verbose:
                        console.print(line, end="", highlight=False)
                        console.file.flush()

                if verbose:
                    _print_docker_build_footer(success=True)
                logger.debug(f"Successfully built {image_name}")

            except DockerException as error:
                if verbose:
                    _print_docker_build_footer(success=False)
                error_msg = error.stderr if error.stderr else str(error)

                # Write error to log file
                f.write(f"\n\nERROR: {error_msg}\n")

                action = "build and push" if push else "build"
                raise DockerBuildError(
                    f"Docker {action} failed. Check build logs: {log_file}"
                ) from error

    return image_name


def run_agent(config_path: str, debug_config: "DebugConfig | None" = None):
    """Run an agent locally from the given config"""
    import sys
    import signal
    import asyncio

    # Lazy import of run_handlers - it has heavy temporal deps
    from terminaluse.lib.cli.handlers.run_handlers import RunError, run_agent as _run_agent

    logger = _get_logger()

    # Flag to track if we're shutting down
    shutting_down = False

    def signal_handler(signum, _frame):
        """Handle signals by raising KeyboardInterrupt"""
        nonlocal shutting_down
        if shutting_down:
            # If we're already shutting down and get another signal, force exit
            logger.info(f"Force exit on signal {signum}")
            sys.exit(1)

        shutting_down = True
        logger.info(f"Received signal {signum}, shutting down...")
        raise KeyboardInterrupt()

    # Set up signal handling for the main thread
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(_run_agent(config_path, debug_config))
    except KeyboardInterrupt:
        logger.info("Shutdown completed.")
        sys.exit(0)
    except RunError as e:
        raise RuntimeError(str(e)) from e
