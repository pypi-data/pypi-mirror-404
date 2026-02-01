import asyncio
import base64
import json
import os

from terminaluse import AsyncTerminalUse
from terminaluse.core.api_error import ApiError
from terminaluse.lib.environment_variables import EnvironmentVariables
from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)


class PermanentRegistrationError(Exception):
    """Registration failed with a permanent error that won't resolve with retries.

    This indicates a configuration issue or that the branch/agent no longer exists.
    The container should exit immediately without retrying.
    """

    pass


def get_auth_principal(env_vars: EnvironmentVariables):
    if not env_vars.TERMINALUSE_AUTH_PRINCIPAL_B64:
        return None

    try:
        decoded_str = base64.b64decode(env_vars.TERMINALUSE_AUTH_PRINCIPAL_B64).decode("utf-8")
        return json.loads(decoded_str)
    except Exception:
        return None


def get_build_info():
    build_info_path = os.environ.get("TERMINALUSE_BUILD_INFO_PATH")
    logger.info(f"Getting build info from {build_info_path}")
    if not build_info_path:
        return None
    try:
        with open(build_info_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


async def register_agent(env_vars: EnvironmentVariables):
    """Register this container with the TerminalUse server.

    This function registers the container's branch/version with the platform.
    The container must have TERMINALUSE_BRANCH_ID and TERMINALUSE_VERSION_ID environment
    variables set (provided by the platform during deployment via Helm).

    On success, stores agent_id, agent_name, agent_api_key, and branch_id
    in environment variables for use by the application.
    """
    if not env_vars.TERMINALUSE_BASE_URL:
        logger.warning("TERMINALUSE_BASE_URL is not set, skipping registration")
        return

    # Branch context is required - these are set by the platform during deploy
    if not env_vars.TERMINALUSE_BRANCH_ID or not env_vars.TERMINALUSE_VERSION_ID:
        logger.warning(
            "TERMINALUSE_BRANCH_ID or TERMINALUSE_VERSION_ID not set, skipping registration. "
            "These are required for branch-based registration."
        )
        return

    # Build the agent's ACP URL
    full_acp_url = f"{env_vars.TERMINALUSE_ACP_URL.rstrip('/')}:{env_vars.TERMINALUSE_ACP_PORT}"

    # Registration data for error messages
    registration_data = {
        "branch_id": env_vars.TERMINALUSE_BRANCH_ID,
        "version_id": env_vars.TERMINALUSE_VERSION_ID,
        "acp_url": full_acp_url,
    }

    # Retry logic with configurable attempts and delay
    # Only transient errors (5xx, connection issues) are retried
    # Permanent errors (4xx) fail immediately
    max_retries = 5
    base_delay = 5  # seconds
    last_exception: Exception | None = None

    attempt = 0
    while attempt < max_retries:
        try:
            # Create SDK client without auth (registration endpoint is whitelisted)
            # Pass empty string to prevent fallback to TERMINALUSE_AGENT_API_KEY env var
            client = AsyncTerminalUse(
                base_url=env_vars.TERMINALUSE_BASE_URL,
                agent_api_key="",
            )
            result = await client.versions.register(
                branch_id=env_vars.TERMINALUSE_BRANCH_ID,
                version_id=env_vars.TERMINALUSE_VERSION_ID,
                acp_url=full_acp_url,
                # No auth header needed - client created with agent_api_key=None
            )

            # Extract agent info from response
            agent_id = result.agent_id
            agent_name = result.agent_name
            agent_api_key = result.agent_api_key
            branch_id = result.branch_id

            # Store in environment for application use
            os.environ["TERMINALUSE_AGENT_ID"] = agent_id
            os.environ["TERMINALUSE_AGENT_NAME"] = agent_name
            os.environ["TERMINALUSE_AGENT_API_KEY"] = agent_api_key
            os.environ["TERMINALUSE_BRANCH_ID"] = branch_id

            # Update env_vars object
            env_vars.TERMINALUSE_AGENT_ID = agent_id
            env_vars.TERMINALUSE_AGENT_NAME = agent_name
            env_vars.TERMINALUSE_AGENT_API_KEY = agent_api_key
            env_vars.TERMINALUSE_BRANCH_ID = branch_id

            # Update the cached environment variables so sandbox has access
            EnvironmentVariables.set_cached(env_vars)

            logger.info(
                f"Successfully registered container for branch '{branch_id}' "
                f"agent '{agent_name}' with acp_url: {full_acp_url}"
            )
            return  # Success, exit the retry loop

        except PermanentRegistrationError:
            # Re-raise permanent errors immediately without retry
            raise

        except ApiError as e:
            # Handle HTTP errors from SDK
            status_code = e.status_code or 500
            response_text = str(e.body)

            if 400 <= status_code < 500:
                # 4xx errors are permanent - don't retry
                error_msg = _get_permanent_error_message(status_code, response_text, registration_data)
                logger.error(f"Permanent registration failure: {error_msg}")
                raise PermanentRegistrationError(error_msg) from e
            else:
                # 5xx errors are transient - retry
                error_msg = f"Server error during registration. Status: {status_code}, Response: {response_text}"
                logger.warning(f"Transient registration failure (attempt {attempt + 1}/{max_retries}): {error_msg}")
                last_exception = e

        except Exception as e:
            # Connection errors and other transient failures - retry
            logger.warning(
                f"Connection error during registration (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}"
            )
            last_exception = e

        attempt += 1
        if attempt < max_retries:
            delay = attempt * base_delay  # 5, 10, 15, 20, 25 seconds
            logger.info(f"Retrying registration in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)

    # If we get here, all retries failed (transient errors only)
    logger.error(
        f"Failed to register container after {max_retries} attempts. "
        f"This may indicate nucleus is down or unreachable. "
        f"The container will exit and K8s will restart it with backoff."
    )
    raise last_exception or Exception(f"Failed to register container after {max_retries} attempts")


def _get_permanent_error_message(status_code: int, response_text: str, registration_data: dict) -> str:
    """Generate a helpful error message for permanent registration failures."""
    branch_id = registration_data.get("branch_id", "unknown")
    version_id = registration_data.get("version_id", "unknown")

    if status_code == 404:
        return (
            f"Branch not found (HTTP 404). "
            f"The branch '{branch_id}' may have been deleted from nucleus. "
            f"This container should be removed. Response: {response_text}"
        )
    elif status_code == 400:
        return (
            f"Invalid registration request (HTTP 400). "
            f"Check that branch_id='{branch_id}' and version_id='{version_id}' are valid. "
            f"Response: {response_text}"
        )
    elif status_code == 401 or status_code == 403:
        return (
            f"Authentication/authorization failed (HTTP {status_code}). "
            f"The container may not have valid credentials. Response: {response_text}"
        )
    elif status_code == 422:
        return f"Validation error (HTTP 422). " f"The registration data is malformed. Response: {response_text}"
    else:
        return (
            f"Registration rejected (HTTP {status_code}). "
            f"This is a permanent failure that won't resolve with retries. "
            f"Response: {response_text}"
        )
