from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

# Lazy imports for faster CLI startup
if TYPE_CHECKING:
    pass

from terminaluse.lib.utils.model_utils import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger
    return make_logger(__name__)


class EnvVarKeys(str, Enum):
    ENVIRONMENT = "ENVIRONMENT"
    TERMINALUSE_TEMPORAL_ADDRESS = "TERMINALUSE_TEMPORAL_ADDRESS"
    TERMINALUSE_BASE_URL = "TERMINALUSE_BASE_URL"
    TERMINALUSE_AUTH_URL = "TERMINALUSE_AUTH_URL"
    # Branch Identifiers (set by platform during deploy)
    TERMINALUSE_BRANCH_ID = "TERMINALUSE_BRANCH_ID"
    TERMINALUSE_VERSION_ID = "TERMINALUSE_VERSION_ID"
    # Agent Identifiers
    TERMINALUSE_AGENT_NAME = "TERMINALUSE_AGENT_NAME"
    TERMINALUSE_AGENT_DESCRIPTION = "TERMINALUSE_AGENT_DESCRIPTION"
    TERMINALUSE_AGENT_ID = "TERMINALUSE_AGENT_ID"
    TERMINALUSE_AGENT_API_KEY = "TERMINALUSE_AGENT_API_KEY"
    # ACP Configuration
    TERMINALUSE_ACP_URL = "TERMINALUSE_ACP_URL"
    TERMINALUSE_ACP_PORT = "TERMINALUSE_ACP_PORT"
    TERMINALUSE_ACP_TYPE = "TERMINALUSE_ACP_TYPE"
    # Workflow Configuration
    TERMINALUSE_WORKFLOW_NAME = "TERMINALUSE_WORKFLOW_NAME"
    TERMINALUSE_WORKFLOW_TASK_QUEUE = "TERMINALUSE_WORKFLOW_TASK_QUEUE"
    # Temporal Worker Configuration
    TERMINALUSE_HEALTH_CHECK_PORT = "TERMINALUSE_HEALTH_CHECK_PORT"
    # Auth Configuration
    TERMINALUSE_AUTH_PRINCIPAL_B64 = "TERMINALUSE_AUTH_PRINCIPAL_B64"
    # Build Information
    TERMINALUSE_BUILD_INFO_PATH = "TERMINALUSE_BUILD_INFO_PATH"
    TERMINALUSE_DATA_ROOT_PATH = "TERMINALUSE_DATA_ROOT_PATH"


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "development"
    STAGING = "staging"
    PROD = "production"


refreshed_environment_variables: EnvironmentVariables | None = None


class EnvironmentVariables(BaseModel):
    ENVIRONMENT: str = Environment.DEV
    TERMINALUSE_TEMPORAL_ADDRESS: str | None = "localhost:7233"
    TERMINALUSE_BASE_URL: str | None = "http://localhost:5003"
    # Branch Identifiers (set by platform during deploy)
    TERMINALUSE_BRANCH_ID: str | None = None
    TERMINALUSE_VERSION_ID: str | None = None
    # Agent Identifiers
    TERMINALUSE_AGENT_NAME: str
    TERMINALUSE_AGENT_DESCRIPTION: str | None = None
    TERMINALUSE_AGENT_ID: str | None = None
    TERMINALUSE_AGENT_API_KEY: str | None = None
    TERMINALUSE_ACP_TYPE: str | None = "async"
    # ACP Configuration
    TERMINALUSE_ACP_URL: str
    TERMINALUSE_ACP_PORT: int = 8000
    # Workflow Configuration
    TERMINALUSE_WORKFLOW_TASK_QUEUE: str | None = None
    TERMINALUSE_WORKFLOW_NAME: str | None = None
    # Temporal Worker Configuration
    TERMINALUSE_HEALTH_CHECK_PORT: int = 80
    # Auth Configuration
    TERMINALUSE_AUTH_PRINCIPAL_B64: str | None = None
    # Build Information
    TERMINALUSE_BUILD_INFO_PATH: str | None = None
    TERMINALUSE_DATA_ROOT_PATH: str | None = None  # Defaults to /bucket_data if not set

    @classmethod
    def refresh(cls) -> EnvironmentVariables:
        global refreshed_environment_variables
        if refreshed_environment_variables is not None:
            return refreshed_environment_variables

        logger = _get_logger()
        logger.info("Refreshing environment variables")
        if os.environ.get(EnvVarKeys.ENVIRONMENT) == Environment.DEV:
            # Lazy import dotenv - only needed when loading env files
            from dotenv import load_dotenv

            # Load global .env file first
            global_env_path = PROJECT_ROOT / ".env"
            if global_env_path.exists():
                logger.debug(f"Loading global environment variables FROM: {global_env_path}")
                load_dotenv(dotenv_path=global_env_path, override=False)

            # Load local project .env.local file (takes precedence)
            local_env_path = Path.cwd().parent / ".env.local"
            if local_env_path.exists():
                logger.debug(f"Loading local environment variables FROM: {local_env_path}")
                load_dotenv(dotenv_path=local_env_path, override=True)

        # Create kwargs dict with environment variables, using None for missing values
        # Pydantic will use the default values when None is passed for optional fields
        kwargs = {}
        for key in EnvVarKeys:
            env_value = os.environ.get(key.value)
            if env_value is not None:
                kwargs[key.value] = env_value

        environment_variables = EnvironmentVariables(**kwargs)
        refreshed_environment_variables = environment_variables
        return refreshed_environment_variables

    @classmethod
    def set_cached(cls, env_vars: EnvironmentVariables) -> None:
        """Set the cached environment variables.

        This is used by registration to update the cache after receiving
        the agent API key from the server.
        """
        global refreshed_environment_variables
        refreshed_environment_variables = env_vars
