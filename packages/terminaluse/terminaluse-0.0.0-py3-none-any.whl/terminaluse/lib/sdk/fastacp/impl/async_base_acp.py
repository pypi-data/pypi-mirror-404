from __future__ import annotations

from typing import Any
from typing_extensions import override

from terminaluse.types.event import Event
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sandbox.config import SandboxConfig
from terminaluse.lib.types.task_context import TaskContext
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer

logger = make_logger(__name__)

# =============================================================================
# Default handlers as top-level functions
#
# These must be defined at module scope (not as nested functions inside a class
# method) so they pass sandbox validation. The sandbox requires handlers to be
# importable by module + function name, which only works for top-level functions.
# Nested functions have __qualname__ containing "<locals>" and cannot be imported.
# =============================================================================

# Module-level client for default handlers (lazily initialized).
# Needed because top-level functions can't access `self._terminaluse_client`.
_default_terminaluse_client = None


def _get_default_terminaluse_client():
    """Get or create the default TerminalUse client for default handlers."""
    global _default_terminaluse_client
    if _default_terminaluse_client is None:
        _default_terminaluse_client = create_async_terminaluse_client()
    return _default_terminaluse_client


async def _default_handle_create(ctx: TaskContext, params: dict[str, Any]) -> None:
    """Default create task handler - logs the task creation."""
    logger.info(f"AsyncBaseACP creating task {ctx.task.id}")


async def _default_handle_event(ctx: TaskContext, event: Event) -> None:
    """Default event handler - logs the event and commits cursor."""
    logger.info(
        f"AsyncBaseACP received event for task {ctx.task.id}: {event.id}, content: {event.content}"
    )
    # Commit cursor to mark event as processed
    client = _get_default_terminaluse_client()
    await client.tracker.update(
        tracker_id=ctx.task.id,
        last_processed_event_id=event.id,
    )


async def _default_handle_cancel(ctx: TaskContext) -> None:
    """Default cancel handler - logs the cancellation."""
    logger.info(f"AsyncBaseACP canceling task {ctx.task.id}")


# =============================================================================
# AsyncBaseACP class
# =============================================================================


class AsyncBaseACP(BaseACPServer):
    """
    AsyncBaseACP implementation - a synchronous ACP that provides basic functionality
    without any special async orchestration like Temporal.

    This implementation provides simple synchronous processing of tasks
    and is suitable for basic agent implementations.
    """

    def __init__(self, sandbox_config: SandboxConfig | None = None):
        super().__init__(sandbox_config=sandbox_config)
        self._setup_handlers()

    @classmethod
    @override
    def create(cls, sandbox_config: SandboxConfig | None = None, **kwargs: Any) -> "AsyncBaseACP":
        """Create and initialize AsyncBaseACP instance

        Args:
            sandbox_config: Optional sandbox configuration
            **kwargs: Additional configuration parameters

        Returns:
            Initialized AsyncBaseACP instance
        """
        logger.info("Initializing AsyncBaseACP instance")
        instance = cls(sandbox_config=sandbox_config)
        logger.info("AsyncBaseACP instance initialized with default handlers")
        return instance

    @override
    def _setup_handlers(self):
        """Set up default handlers using top-level functions for sandbox compatibility.

        We register top-level functions (defined above) instead of using nested
        functions with decorators. This ensures handlers pass sandbox validation
        and can be overwritten by user handlers without generating false warnings.
        """
        self.on_create(_default_handle_create)
        self.on_event(_default_handle_event)
        self.on_cancel(_default_handle_cancel)


AgenticBaseACP = AsyncBaseACP
