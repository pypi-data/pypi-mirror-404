"""Deploy handlers for the new platform-based deployment flow.

The CLI no longer executes Helm commands directly. Instead:
1. CLI builds and pushes Docker images to platform-managed registry
2. CLI calls platform API to trigger deployment
3. Platform (nucleus) handles all Helm/K8s operations
"""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from pydantic import Field, BaseModel
from rich.console import Console
from python_on_whales import docker

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.exceptions import DeploymentError
from terminaluse.lib.sdk.config.deployment_config import EnvironmentDeploymentConfig

if TYPE_CHECKING:
    from terminaluse import TerminalUse

logger = make_logger(__name__)
console = Console()

# Deployment polling configuration
DEFAULT_DEPLOY_TIMEOUT = 300  # 5 minutes
DEFAULT_POLL_INTERVAL = 2  # seconds


class DeployConfig(BaseModel):
    """Configuration for platform deployment API."""

    replicas: int = Field(default=1, description="Number of replicas")
    resources: dict[str, Any] = Field(default_factory=dict, description="Resource requests/limits")


def docker_login(registry: str, username: str, password: str) -> None:
    """Login to Docker registry using platform-provided credentials.

    Args:
        registry: Registry URL (e.g., "us-east4-docker.pkg.dev")
        username: Registry username (typically "oauth2accesstoken")
        password: Registry token/password
    """
    import subprocess

    try:
        # Use subprocess to suppress "Login Succeeded" message
        subprocess.run(
            ["docker", "login", registry, "-u", username, "--password-stdin"],
            input=password,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Successfully logged in to registry: {registry}")
    except subprocess.CalledProcessError as e:
        raise DeploymentError(f"Failed to login to registry {registry}: {e.stderr}") from e
    except Exception as e:
        raise DeploymentError(f"Failed to login to registry {registry}: {e}") from e


def docker_logout(registry: str) -> None:
    """Logout from Docker registry.

    Args:
        registry: Registry URL to logout from
    """
    import subprocess

    try:
        # Use subprocess directly to suppress docker CLI output
        subprocess.run(
            ["docker", "logout", registry],
            capture_output=True,
            check=True,
        )
    except Exception as e:
        logger.warning(f"Failed to logout from registry {registry}: {e}")


def poll_deployment_status(
    client: "TerminalUse",
    branch_id: str,
    timeout: int = DEFAULT_DEPLOY_TIMEOUT,
    interval: int = DEFAULT_POLL_INTERVAL,
) -> Any:
    """Poll branch status until ready, failed, or timeout.

    Uses auto-generated client.branches.retrieve() API.

    Args:
        client: TerminalUse client instance
        branch_id: ID of the branch to poll
        timeout: Maximum time to wait in seconds (default: 300)
        interval: Polling interval in seconds (default: 2)

    Returns:
        Final branch status object

    Raises:
        DeploymentError: If deployment times out
    """
    # Terminal states that indicate deployment is done (success or failure)
    # These are VersionStatus values (from current_version.status)
    terminal_states = {"active", "failed", "unhealthy", "retired", "rolled_back"}

    start = time.time()
    console.print("Waiting for deployment", end="")
    last_status = None

    while time.time() - start < timeout:
        try:
            branch = client.branches.retrieve(branch_id)
            # Get status from current_version (Version now holds the status)
            if branch.current_version:
                current_status = branch.current_version.status.lower()
            else:
                current_status = "deploying"
            last_status = current_status

            if current_status in terminal_states:
                console.print()  # Newline after dots
                return branch

            # Still deploying, continue polling
            console.print(".", end="")
            time.sleep(interval)

        except Exception as e:
            logger.warning(f"Error polling deployment status: {e}")
            console.print("x", end="")  # Show error indicator
            time.sleep(interval)

    console.print()  # Newline after dots
    raise DeploymentError(f"Deployment timed out after {timeout} seconds (last status: {last_status})")


def build_deploy_config(env_config: EnvironmentDeploymentConfig, is_production: bool = False) -> dict[str, Any]:
    """Build deployment configuration from resolved environment config.

    Args:
        env_config: Environment-specific deployment config (production or preview)
        is_production: Whether this is a production environment (affects are_tasks_sticky default)

    Returns:
        Configuration dict for POST /agents/deploy API
    """
    # Resolve are_tasks_sticky default based on environment type
    are_tasks_sticky = env_config.areTasksSticky
    if are_tasks_sticky is None:
        are_tasks_sticky = is_production  # Production defaults to True, preview to False

    return {
        "replicas": env_config.replicaCount,
        "resources": {
            "requests": {
                "cpu": env_config.resources.requests.cpu,
                "memory": env_config.resources.requests.memory,
            },
            "limits": {
                "cpu": env_config.resources.limits.cpu,
                "memory": env_config.resources.limits.memory,
            },
        },
        "are_tasks_sticky": are_tasks_sticky,
    }


def validate_docker_running() -> bool:
    """Check if Docker daemon is running.

    Returns:
        True if Docker is available and running
    """
    try:
        docker.info()
        return True
    except Exception:
        return False


def check_dockerfile_exists(manifest_path: str) -> bool:
    """Check if Dockerfile exists in the manifest directory.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        True if Dockerfile exists
    """
    from pathlib import Path

    manifest_dir = Path(manifest_path).parent
    dockerfile_path = manifest_dir / "Dockerfile"
    return dockerfile_path.exists()
