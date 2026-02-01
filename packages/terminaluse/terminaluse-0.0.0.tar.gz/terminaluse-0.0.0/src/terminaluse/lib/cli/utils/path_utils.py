from __future__ import annotations

from typing import Dict
from pathlib import Path

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sdk.config.agent_manifest import AgentManifest

logger = make_logger(__name__)


class PathResolutionError(Exception):
    """An error occurred during path resolution"""


def resolve_and_validate_path(base_path: Path, configured_path: str, file_type: str) -> Path:
    """Resolve and validate a configured path"""
    path_obj = Path(configured_path)

    if path_obj.is_absolute():
        # Absolute path - resolve to canonical form
        resolved_path = path_obj.resolve()
    else:
        # Relative path - resolve relative to manifest directory
        resolved_path = (base_path / configured_path).resolve()

    # Validate the file exists
    if not resolved_path.exists():
        raise PathResolutionError(
            f"{file_type} file not found: {resolved_path}\n"
            f"  Configured path: {configured_path}\n"
            f"  Resolved from manifest: {base_path}"
        )

    # Validate it's actually a file
    if not resolved_path.is_file():
        raise PathResolutionError(f"{file_type} path is not a file: {resolved_path}")

    return resolved_path


def validate_path_security(resolved_path: Path, manifest_dir: Path) -> None:
    """Basic security validation for resolved paths"""
    try:
        # Ensure the resolved path is accessible
        resolved_path.resolve()

        # Optional: Add warnings for paths that go too far up
        try:
            # Check if path goes more than 3 levels up from manifest
            relative_to_manifest = resolved_path.relative_to(manifest_dir.parent.parent.parent)
            if str(relative_to_manifest).startswith(".."):
                logger.warning(f"Path goes significantly outside project structure: {resolved_path}")
        except ValueError:
            # Path is outside the tree - that's okay, just log it
            logger.info(f"Using path outside manifest directory tree: {resolved_path}")

    except Exception as e:
        raise PathResolutionError(f"Path resolution failed: {resolved_path} - {str(e)}") from e


def get_file_paths(manifest: AgentManifest, manifest_path: str) -> Dict[str, Path | None]:
    """Get resolved file paths from manifest configuration"""
    manifest_dir = Path(manifest_path).parent.resolve()

    # Use default hardcoded structure for local development
    src_dir = manifest_dir / "src"
    agent_path = (src_dir / "agent.py").resolve()
    worker_path = (src_dir / "run_worker.py").resolve() if manifest.agent.is_temporal_agent() else None

    # Validate paths
    if not agent_path.exists():
        raise PathResolutionError(f"Agent file not found: {agent_path}")

    if worker_path and not worker_path.exists():
        raise PathResolutionError(f"Worker file not found: {worker_path}")

    return {
        "agent": agent_path,
        "worker": worker_path,
        "agent_dir": agent_path.parent,
        "worker_dir": worker_path.parent if worker_path else None,
    }


def calculate_uvicorn_target_for_local(agent_path: Path, manifest_dir: Path) -> str:
    """Calculate the uvicorn target path for local development"""
    # Ensure both paths are resolved to canonical form for accurate comparison
    agent_resolved = agent_path.resolve()
    manifest_resolved = manifest_dir.resolve()

    try:
        # Try to use path relative to manifest directory
        agent_relative = agent_resolved.relative_to(manifest_resolved)
        # Convert to module notation: src/agent.py -> src.agent
        module_path = str(agent_relative.with_suffix(""))  # Remove .py extension
        module_path = module_path.replace("/", ".")  # Convert slashes to dots
        module_path = module_path.replace("\\", ".")  # Handle Windows paths
        return module_path
    except ValueError:
        # Path cannot be made relative - use absolute file path
        logger.warning(
            f"Agent file {agent_resolved} cannot be made relative to manifest directory {manifest_resolved}, using absolute file path"
        )
        return str(agent_resolved)


def calculate_docker_agent_module(manifest: AgentManifest, manifest_path: str) -> str:
    """Calculate the Python module path for the agent file in the Docker container

    This should return the same module notation as local development for consistency.
    """
    # Use the same logic as local development
    manifest_dir = Path(manifest_path).parent

    # Use default agent path
    agent_config_path = "src/agent.py"

    # Resolve to actual file path
    agent_path = resolve_and_validate_path(manifest_dir, agent_config_path, "Agent")

    # Use the same module calculation as local development
    return calculate_uvicorn_target_for_local(agent_path, manifest_dir)
