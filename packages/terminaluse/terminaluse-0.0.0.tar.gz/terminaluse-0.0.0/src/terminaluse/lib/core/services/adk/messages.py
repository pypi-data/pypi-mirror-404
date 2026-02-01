from __future__ import annotations

import asyncio
from typing import Any, Coroutine

from terminaluse import AsyncTerminalUse
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import heartbeat_if_in_workflow
from terminaluse.types.task_message import TaskMessage, TaskMessageContent
from terminaluse.lib.core.tracing.tracer import AsyncTracer
from terminaluse.lib.types import TaskMessageUpdate
from terminaluse.types import TaskMessageUpdate_Full
from terminaluse.lib.core.services.adk.streaming import StreamingService

logger = make_logger(__name__)


class MessagesService:
    def __init__(
        self,
        terminaluse_client: AsyncTerminalUse,
        streaming_service: StreamingService,
        tracer: AsyncTracer,
    ):
        self._terminaluse_client = terminaluse_client
        self._streaming_service = streaming_service
        self._tracer = tracer

    async def send(
        self,
        task_id: str,
        content: TaskMessageContent,
        emit_updates: bool = True,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> TaskMessage:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="messages.send",
            input={"task_id": task_id, "message": content},
        ) as span:
            heartbeat_if_in_workflow("create message")
            task_message = await self._terminaluse_client.messages.create(
                task_id=task_id,
                content=content,
            )
            if emit_updates:
                await self._emit_updates([task_message])
            if span:
                span.output = task_message.model_dump()
            return task_message

    async def update_message(
        self,
        task_id: str,
        message_id: str,
        content: TaskMessageContent,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> TaskMessage:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="update_message",
            input={
                "task_id": task_id,
                "message_id": message_id,
                "message": content,
            },
        ) as span:
            heartbeat_if_in_workflow("update message")
            task_message = await self._terminaluse_client.messages.update(
                task_id=task_id,
                message_id=message_id,
                content=content,
            )
            if span:
                span.output = task_message.model_dump()
            return task_message

    async def send_batch(
        self,
        task_id: str,
        contents: list[TaskMessageContent],
        emit_updates: bool = True,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> list[TaskMessage]:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="messages.send_batch",
            input={"task_id": task_id, "messages": contents},
        ) as span:
            heartbeat_if_in_workflow("create messages batch")
            task_messages = await self._terminaluse_client.messages.batch.create(
                task_id=task_id,
                contents=contents,
            )
            if emit_updates:
                await self._emit_updates(task_messages)
            if span:
                span.output = {"messages": [task_message.model_dump() for task_message in task_messages]}
            return task_messages

    async def update_messages_batch(
        self,
        task_id: str,
        updates: dict[str, TaskMessageContent],
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> list[TaskMessage]:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="update_messages_batch",
            input={"task_id": task_id, "updates": updates},
        ) as span:
            heartbeat_if_in_workflow("update messages batch")
            task_messages = await self._terminaluse_client.messages.batch.update(
                task_id=task_id,
                updates=updates,
            )
            if span:
                span.output = {"messages": [task_message.model_dump() for task_message in task_messages]}
            return task_messages

    async def list_messages(
        self,
        task_id: str,
        limit: int | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> list[TaskMessage]:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="list_messages",
            input={"task_id": task_id, "limit": limit},
        ) as span:
            heartbeat_if_in_workflow("list messages")
            task_messages = await self._terminaluse_client.messages.list(
                task_id=task_id,
                limit=limit,
            )
            if span:
                span.output = {"messages": [task_message.model_dump() for task_message in task_messages]}
            return task_messages

    async def _emit_updates(self, task_messages: list[TaskMessage]) -> None:
        stream_update_handlers: list[Coroutine[Any, Any, TaskMessageUpdate | None]] = []
        for task_message in task_messages:
            stream_update_handler = self._streaming_service.stream_update(
                update=TaskMessageUpdate_Full(
                    parent_task_message=task_message,
                    content=task_message.content,
                )
            )
            stream_update_handlers.append(stream_update_handler)

        await asyncio.gather(*stream_update_handlers)
