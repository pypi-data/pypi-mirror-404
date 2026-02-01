from __future__ import annotations

import json

from terminaluse import AsyncTerminalUse
from terminaluse.lib.utils.logging import make_logger
from terminaluse.types.task_message import (
    TaskMessage,
    TaskMessageContent,
)
from terminaluse.types.task_message_content import (
    TaskMessageContent_Data,
    TaskMessageContent_Reasoning,
    TaskMessageContent_Text,
    TaskMessageContent_ToolRequest,
    TaskMessageContent_ToolResponse,
)
from terminaluse.types.task_message_delta import (
    TaskMessageDelta,
    TaskMessageDelta_Data,
    TaskMessageDelta_Text,
    TaskMessageDelta_ToolRequest,
    TaskMessageDelta_ToolResponse,
    TaskMessageDelta_ReasoningContent,
    TaskMessageDelta_ReasoningSummary,
)
from terminaluse.lib.types import TaskMessageUpdate
from terminaluse.types import (
    TaskMessageUpdate_Done,
    TaskMessageUpdate_Full,
    TaskMessageUpdate_Delta,
    TaskMessageUpdate_Start,
)

logger = make_logger(__name__)


class DeltaAccumulator:
    """Accumulates streaming deltas into final content. Supports multiple content types."""

    def __init__(self):
        self._text_deltas: list[TaskMessageDelta_Text] = []
        self._data_deltas: list[TaskMessageDelta_Data] = []
        self._tool_request_deltas: list[TaskMessageDelta_ToolRequest] = []
        self._tool_response_deltas: list[TaskMessageDelta_ToolResponse] = []
        self._reasoning_summaries: dict[int, str] = {}
        self._reasoning_contents: dict[int, str] = {}

    def add_delta(self, delta: TaskMessageDelta):
        """Add a delta to the accumulator."""
        if isinstance(delta, TaskMessageDelta_Text):
            self._text_deltas.append(delta)
        elif isinstance(delta, TaskMessageDelta_Data):
            self._data_deltas.append(delta)
        elif isinstance(delta, TaskMessageDelta_ToolRequest):
            self._tool_request_deltas.append(delta)
        elif isinstance(delta, TaskMessageDelta_ToolResponse):
            self._tool_response_deltas.append(delta)
        elif isinstance(delta, TaskMessageDelta_ReasoningSummary):
            if delta.summary_index not in self._reasoning_summaries:
                self._reasoning_summaries[delta.summary_index] = ""
            self._reasoning_summaries[delta.summary_index] += delta.summary_delta or ""
        elif isinstance(delta, TaskMessageDelta_ReasoningContent):
            if delta.content_index not in self._reasoning_contents:
                self._reasoning_contents[delta.content_index] = ""
            self._reasoning_contents[delta.content_index] += delta.content_delta or ""

    def has_deltas(self) -> bool:
        """Check if any deltas have been accumulated."""
        return bool(
            self._text_deltas
            or self._data_deltas
            or self._tool_request_deltas
            or self._tool_response_deltas
            or self._reasoning_summaries
            or self._reasoning_contents
        )

    def convert_to_content(self) -> TaskMessageContent:
        """Convert accumulated deltas to content. Returns text content if available."""
        if self._text_deltas:
            return TaskMessageContent_Text(
                author="agent",
                content="".join(delta.text_delta or "" for delta in self._text_deltas),
            )
        if self._data_deltas:
            data_str = "".join(delta.data_delta or "" for delta in self._data_deltas)
            return TaskMessageContent_Data(author="agent", data=json.loads(data_str))
        if self._tool_request_deltas:
            args_str = "".join(delta.arguments_delta or "" for delta in self._tool_request_deltas)
            return TaskMessageContent_ToolRequest(
                author="agent",
                tool_call_id=self._tool_request_deltas[0].tool_call_id,
                name=self._tool_request_deltas[0].name,
                arguments=json.loads(args_str),
            )
        if self._tool_response_deltas:
            return TaskMessageContent_ToolResponse(
                author="agent",
                tool_call_id=self._tool_response_deltas[0].tool_call_id,
                name=self._tool_response_deltas[0].name,
                content="".join(delta.content_delta or "" for delta in self._tool_response_deltas),
            )
        if self._reasoning_summaries or self._reasoning_contents:
            summary_list = [
                self._reasoning_summaries[i]
                for i in sorted(self._reasoning_summaries.keys())
                if self._reasoning_summaries[i]
            ]
            content_list = [
                self._reasoning_contents[i]
                for i in sorted(self._reasoning_contents.keys())
                if self._reasoning_contents[i]
            ]
            if summary_list or content_list:
                return TaskMessageContent_Reasoning(
                    author="agent",
                    summary=summary_list,
                    content=content_list if content_list else None,
                    style="static",
                )
        return TaskMessageContent_Text(author="agent", content="")


class StreamingTaskMessageContext:
    def __init__(
        self,
        task_id: str,
        initial_content: TaskMessageContent,
        terminaluse_client: AsyncTerminalUse,
        streaming_service: "StreamingService",
    ):
        self.task_id = task_id
        self.initial_content = initial_content
        self.task_message: TaskMessage | None = None
        self._terminaluse_client = terminaluse_client
        self._streaming_service = streaming_service
        self._is_closed = False
        self._delta_accumulator = DeltaAccumulator()

    async def __aenter__(self) -> "StreamingTaskMessageContext":
        return await self.open()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.close()

    async def open(self) -> "StreamingTaskMessageContext":
        self._is_closed = False

        self.task_message = await self._terminaluse_client.messages.create(
            task_id=self.task_id,
            content=self.initial_content,
            streaming_status="IN_PROGRESS",
        )

        # Send the START event
        start_event = TaskMessageUpdate_Start(
            parent_task_message=self.task_message,
            content=self.initial_content,
        )
        await self._streaming_service.stream_update(start_event)
        logger.info(f"Streaming context opened for task {self.task_id}")

        return self

    async def close(self) -> TaskMessage:
        """Close the streaming context."""
        if not self.task_message:
            raise ValueError("Context not properly initialized - no task message")

        if self._is_closed:
            return self.task_message  # Already done

        # Send the DONE event
        done_event = TaskMessageUpdate_Done(
            parent_task_message=self.task_message,
        )
        await self._streaming_service.stream_update(done_event)

        # Update the task message with the final content
        if self._delta_accumulator.has_deltas():
            self.task_message.content = self._delta_accumulator.convert_to_content()

        await self._terminaluse_client.messages.update(
            task_id=self.task_id,
            message_id=self.task_message.id,
            content=self.task_message.content,
            streaming_status="DONE",
        )

        # Mark the context as done
        self._is_closed = True
        logger.info(f"Streaming context closed for task {self.task_id}")
        return self.task_message

    async def stream_update(self, update: TaskMessageUpdate) -> TaskMessageUpdate | None:
        """Stream an update to the repository."""
        if self._is_closed:
            raise ValueError("Context is already done")

        if not self.task_message:
            raise ValueError("Context not properly initialized - no task message")

        if isinstance(update, TaskMessageUpdate_Delta):
            if update.delta is not None:
                self._delta_accumulator.add_delta(update.delta)
            # Stream deltas to Redis for real-time display
            return await self._streaming_service.stream_update(update)

        if isinstance(update, TaskMessageUpdate_Done):
            await self.close()
            return update

        if isinstance(update, TaskMessageUpdate_Full):
            # For FULL events: update database but DON'T stream to Redis.
            # The CLI already received content via deltas - sending FULL would duplicate it.
            await self._terminaluse_client.messages.update(
                task_id=self.task_id,
                message_id=update.parent_task_message.id,  # type: ignore[union-attr]
                content=update.content,
                streaming_status="DONE",
            )
            self._is_closed = True
            return update

        # For any other event types, stream to Redis
        return await self._streaming_service.stream_update(update)


class StreamingService:
    """
    Service for streaming task message updates to clients via the backend API.

    Each event is sent immediately via HTTP POST - no batching.
    This ensures reliable delivery in short-lived sandbox handlers.
    """

    # Maximum retry attempts before dropping events
    MAX_RETRIES = 3

    def __init__(
        self,
        terminaluse_client: AsyncTerminalUse,
        batch_interval_ms: float = 50.0,  # Kept for API compatibility, but unused
    ):
        """
        Initialize the streaming service.

        Args:
            terminaluse_client: The TerminalUse API client
            batch_interval_ms: Unused, kept for API compatibility
        """
        self._terminaluse_client = terminaluse_client

    def streaming_task_message_context(
        self,
        task_id: str,
        initial_content: TaskMessageContent,
    ) -> StreamingTaskMessageContext:
        return StreamingTaskMessageContext(
            task_id=task_id,
            initial_content=initial_content,
            terminaluse_client=self._terminaluse_client,
            streaming_service=self,
        )

    async def stream_update(self, update: TaskMessageUpdate) -> TaskMessageUpdate | None:
        """
        Send a stream update to the backend immediately.

        Args:
            update: The update to stream

        Returns:
            The update if sent successfully, None on error
        """
        task_id = update.parent_task_message.task_id  # type: ignore[union-attr]

        try:
            await self._terminaluse_client.stream.events.publish(
                task_id=task_id,
                events=[update],
            )
            return update
        except Exception as e:
            event_type = update.type if hasattr(update, 'type') else type(update).__name__
            logger.error(f"Failed to send stream event: task_id={task_id}, type={event_type}, error={e}")
            return None

    async def flush(self) -> None:
        """No-op for API compatibility. Events are sent immediately, no batching."""
        pass
