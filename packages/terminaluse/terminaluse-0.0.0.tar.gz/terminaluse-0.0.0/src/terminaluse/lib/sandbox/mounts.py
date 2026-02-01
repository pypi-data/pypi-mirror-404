"""
Sandbox mount assembly and bubblewrap integration.

This module provides utilities for:
- Loading manifest and extracting baked mount configurations
- Assembling all mounts (filesystem, system folders, baked) in correct order
- Validating mount configurations for conflicts
- Generating bubblewrap mount arguments
- Writing mount config for debugging/observability
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sdk.config.agent_manifest import AgentManifest
from terminaluse.lib.adk._modules.task import DOT_CLAUDE_CONFIG

logger = make_logger(__name__)

# TERMINALUSE_DATA_ROOT_PATH from environment, defaults to /bucket_data
DATA_ROOT_PATH = os.environ.get("TERMINALUSE_DATA_ROOT_PATH", "/bucket_data")


class MountConflictError(Exception):
    """Raised when two mounts conflict on the same target path."""

    pass


@dataclass
class Mount:
    """Represents a single sandbox mount."""

    host_path: str
    sandbox_path: str
    read_only: bool
    mount_type: str  # "filesystem", "system_folder", "baked"
    mount_depth: int = 0  # For ordering nested mounts


def load_config(agent_workdir: str) -> AgentManifest | None:
    """
    Load config from local filesystem (baked into image).

    Returns None if config doesn't exist or is malformed (lenient during dev).

    Args:
        agent_workdir: Path to agent working directory (e.g., /app/examples/my-agent)

    Returns:
        AgentManifest if successfully loaded, None otherwise
    """
    config_path = os.path.join(agent_workdir, "config.yaml")
    try:
        with open(config_path) as f:
            return AgentManifest.model_validate(yaml.safe_load(f))
    except FileNotFoundError:
        logger.debug(f"No config found at {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse config YAML from {config_path}: {e}")
        return None
    except ValidationError as e:
        logger.warning(f"Failed to validate config from {config_path}: {e}")
        return None


def get_baked_mounts(manifest: AgentManifest | None, agent_workdir: str) -> list[Mount]:
    """
    Get baked mounts from manifest.

    Returns empty list if none configured or manifest is None.

    Args:
        manifest: Loaded agent manifest (or None)
        agent_workdir: Path to agent working directory

    Returns:
        List of Mount objects for baked mounts
    """
    if manifest is None:
        return []

    mount_configs = (
        manifest.sandbox.mounts
        if manifest.sandbox and manifest.sandbox.mounts is not None
        else []
    )

    mounts = []
    for config in mount_configs:
        source_path = os.path.join(agent_workdir, config.source)

        # Only mount if path exists in image
        if os.path.exists(source_path):
            mounts.append(
                Mount(
                    host_path=source_path,
                    sandbox_path=config.target,
                    read_only=config.readonly,
                    mount_type="baked",
                )
            )
        else:
            logger.warning(f"Baked mount source path does not exist: {source_path}")

    return mounts


def _validate_no_conflicts(mounts: list[Mount]) -> None:
    """
    Validate no exact path conflicts (different sources to same target).

    Allows parent/child overlay (e.g., /root/.claude and /root/.claude/skills)
    but not exact duplicates from different sources.

    Args:
        mounts: List of mounts to validate

    Raises:
        MountConflictError: If conflicting mounts are found
    """
    targets: dict[str, Mount] = {}
    for m in mounts:
        if m.sandbox_path in targets:
            existing = targets[m.sandbox_path]
            if existing.host_path != m.host_path:
                raise MountConflictError(
                    f"Conflicting mounts to {m.sandbox_path}: "
                    f"{existing.host_path} vs {m.host_path}"
                )
        targets[m.sandbox_path] = m


def assemble_sandbox_mounts(
    task_id: str,
    filesystem_id: str,
    manifest: AgentManifest | None,
    agent_workdir: str,
) -> list[Mount]:
    """
    Assemble all mounts for sandbox in correct order.

    Mount order (by depth):
    1. Filesystem mount (/workspace) - depth 0
    2. Task system folder (/root/.claude) - depth 0
    3. Agent baked mounts (overlaid on top) - depth 1

    Args:
        task_id: ID of the task
        filesystem_id: ID of the filesystem
        manifest: Loaded agent manifest (or None)
        agent_workdir: Path to agent working directory

    Returns:
        Sorted list of Mount objects

    Raises:
        MountConflictError: If conflicting mounts are detected
    """
    mounts: list[Mount] = []

    # 1. Filesystem mount
    mounts.append(
        Mount(
            host_path=f"{DATA_ROOT_PATH}/filesystems/{filesystem_id}",
            sandbox_path="/workspace",
            read_only=False,
            mount_type="filesystem",
            mount_depth=0,
        )
    )

    # 2. Task system folder (synced from GCS) - uses DOT_CLAUDE_CONFIG from TaskModule
    mounts.append(
        Mount(
            host_path=f"{DATA_ROOT_PATH}/tasks/{task_id}/{DOT_CLAUDE_CONFIG['host_path']}",
            sandbox_path=DOT_CLAUDE_CONFIG["sandbox_mount_path"],
            read_only=False,
            mount_type="system_folder",
            mount_depth=0,
        )
    )

    # 3. Agent baked mounts (from Docker image, overlaid on top)
    baked_mounts = get_baked_mounts(manifest, agent_workdir)
    for mount in baked_mounts:
        mount.mount_depth = 1  # Nested mounts come after parents
        mounts.append(mount)

    # Validate no conflicts before returning
    _validate_no_conflicts(mounts)

    # Sort by depth: parents (0) before children (1)
    return sorted(mounts, key=lambda m: m.mount_depth)


def write_sandbox_mounts_file(task_id: str, mounts: list[Mount]) -> str:
    """
    Write mounts config for debugging and observability.

    This is NOT the primary mechanism for passing mounts to the sandbox.
    Mounts are passed directly to SandboxRunner.run() in memory.
    This file is written for debugging, auditing, and post-mortem analysis.

    Args:
        task_id: ID of the task
        mounts: List of assembled mounts

    Returns:
        Path to the written config file
    """
    config_path = f"{DATA_ROOT_PATH}/tasks/{task_id}/.sandbox_mounts.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    config = {"version": 1, "mounts": [asdict(m) for m in mounts]}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config_path


def configure_bwrap_mounts(mounts: list[Mount]) -> list[str]:
    """
    Generate bubblewrap mount arguments from Mount objects.

    Args:
        mounts: List of mounts (should already be sorted by depth)

    Returns:
        List of bubblewrap command-line arguments for mounts
    """
    args: list[str] = []
    for mount in mounts:  # Already sorted by mount_depth
        # bubblewrap uses separate source and dest arguments (not colon-separated)
        flag = "--ro-bind" if mount.read_only else "--bind"
        args.extend([flag, mount.host_path, mount.sandbox_path])
    return args
