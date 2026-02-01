from terminaluse import AsyncTerminalUse


def create_async_terminaluse_client(**kwargs) -> AsyncTerminalUse:
    """Create an AsyncTerminalUse client.

    The client automatically reads authentication from environment variables:
    - TERMINALUSE_API_KEY: Bearer token for CLI/user authentication
    - TERMINALUSE_AGENT_API_KEY: Agent API key for agent-to-platform authentication

    At least one must be set for authenticated requests.
    """
    return AsyncTerminalUse(**kwargs)
