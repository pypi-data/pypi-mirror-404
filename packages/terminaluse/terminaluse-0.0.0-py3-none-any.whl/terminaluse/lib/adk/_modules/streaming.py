# ruff: noqa: I001
# Import order matters - AsyncTracer must come after client import to avoid circular imports
from __future__ import annotations
from temporalio.common import RetryPolicy

from terminaluse import AsyncTerminalUse  # noqa: F401
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client
from terminaluse.lib.core.services.adk.streaming import (
    StreamingService,
    StreamingTaskMessageContext,
)
from terminaluse.types.task_message_content import TaskMessageContent
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import in_temporal_workflow

logger = make_logger(__name__)

DEFAULT_RETRY_POLICY = RetryPolicy(maximum_attempts=1)


class StreamingModule:
    """
    Module for streaming content to clients in TerminalUse.

    This interface wraps around the StreamingService and provides a high-level API
    for streaming events to clients, supporting both synchronous and asynchronous
    (Temporal workflow) contexts.
    """

    def __init__(self, streaming_service: StreamingService | None = None):
        """
        Initialize the streaming interface.

        Args:
            streaming_service (Optional[StreamingService]): Optional StreamingService instance. If not provided,
                a new service will be created with default parameters.
        """
        if streaming_service is None:
            terminaluse_client = create_async_terminaluse_client()
            self._streaming_service = StreamingService(
                terminaluse_client=terminaluse_client,
            )
        else:
            self._streaming_service = streaming_service

    def streaming_task_message_context(
        self,
        task_id: str,
        initial_content: TaskMessageContent,
    ) -> StreamingTaskMessageContext:
        """
        Create a streaming context for managing TaskMessage lifecycle.

        This is a context manager that automatically creates a TaskMessage, sends START event,
        and sends DONE event when the context exits. Perfect for simple streaming scenarios.

        Args:
            task_id: The ID of the task
            initial_content: The initial content for the TaskMessage
            terminaluse_client: The TerminalUse client for creating/updating messages

        Returns:
            StreamingTaskMessageContext: Context manager for streaming operations
        """
        # Note: We don't support Temporal activities for streaming context methods yet
        # since they involve complex state management across multiple activity calls
        if in_temporal_workflow():
            logger.warning(
                "Streaming context methods are not yet supported in Temporal workflows. "
                "You should wrap the entire streaming context in an activity. All nondeterministic network calls should be wrapped in an activity and generators cannot operate across activities and workflows."
            )

        return self._streaming_service.streaming_task_message_context(
            task_id=task_id,
            initial_content=initial_content,
        )
