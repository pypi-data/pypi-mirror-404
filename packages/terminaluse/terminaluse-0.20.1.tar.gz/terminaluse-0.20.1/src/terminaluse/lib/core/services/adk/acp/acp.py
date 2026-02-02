from __future__ import annotations

from typing import Any

from terminaluse import AsyncTerminalUse
from terminaluse.types.task import Task
from terminaluse.types.event import Event
from terminaluse.core.request_options import RequestOptions
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import heartbeat_if_in_workflow
from terminaluse.lib.core.tracing.tracer import AsyncTracer
from terminaluse.types.task_message_content import TaskMessageContent

logger = make_logger(__name__)


class ACPService:
    def __init__(
        self,
        terminaluse_client: AsyncTerminalUse,
        tracer: AsyncTracer,
    ):
        self._terminaluse_client = terminaluse_client
        self._tracer = tracer

    async def task_create(
        self,
        name: str | None = None,
        agent_id: str | None = None,
        agent_name: str | None = None,
        params: dict[str, Any] | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        request: dict[str, Any] | None = None,
    ) -> Task:
        trace = self._tracer.trace(trace_id=trace_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="task_create",
            input={
                "name": name,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "params": params,
            },
        ) as span:
            heartbeat_if_in_workflow("task create")

            # Extract headers from request; pass-through to agent
            extra_headers = request.get("headers") if request else None
            request_options: RequestOptions | None = {"additional_headers": extra_headers} if extra_headers else None

            if not agent_name and not agent_id:
                raise ValueError("Either agent_name or agent_id must be provided")

            task_response = await self._terminaluse_client.tasks.create(
                agent_name=agent_name,
                agent_id=agent_id,
                name=name,
                params=params,
                request_options=request_options,
            )

            # TaskResponse has the same fields as Task, so we can create a Task from it
            task_entry = Task(
                id=task_response.id,
                status=task_response.status,
                namespace_id=task_response.namespace_id,
                filesystem_id=task_response.filesystem_id,
                name=task_response.name,
                params=task_response.params,
                created_at=task_response.created_at,
                updated_at=task_response.updated_at,
            )
            if span:
                span.output = task_entry.model_dump()
            return task_entry

    async def event_send(
        self,
        content: TaskMessageContent,
        agent_id: str | None = None,
        agent_name: str | None = None,
        task_id: str | None = None,
        task_name: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        request: dict[str, Any] | None = None,
    ) -> Event:
        trace = self._tracer.trace(trace_id=trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="event_send",
            input={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task_id": task_id,
                "task_name": task_name,
                "content": content,
            },
        ) as span:
            heartbeat_if_in_workflow("event send")

            # Extract headers from request; pass-through to agent
            extra_headers = request.get("headers") if request else None
            request_options: RequestOptions | None = {"additional_headers": extra_headers} if extra_headers else None

            if not task_id:
                raise ValueError("task_id must be provided to send an event")

            event_entry = await self._terminaluse_client.tasks.send_event(
                task_id=task_id,
                content=content,
                request_options=request_options,
            )

            if span:
                span.output = event_entry.model_dump()
            return event_entry

    async def task_cancel(
        self,
        task_id: str | None = None,
        task_name: str | None = None,
        agent_id: str | None = None,
        agent_name: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        request: dict[str, Any] | None = None,
    ) -> Task:
        """
        Cancel a task via the SDK.

        Args:
            task_id: ID of the task to cancel
            task_name: Name of the task to cancel (unused, kept for interface compatibility)
            agent_id: ID of the agent (unused, kept for interface compatibility)
            agent_name: Name of the agent (unused, kept for interface compatibility)
            trace_id: Trace ID for tracing
            parent_span_id: Parent span ID for tracing
            request: Additional request context including headers to forward

        Returns:
            Task entry representing the cancelled task

        Raises:
            ValueError: If task_id is not provided
        """
        # Require task identification
        if not task_id:
            raise ValueError("task_id must be provided to cancel a task")

        trace = self._tracer.trace(trace_id=trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="task_cancel",
            input={
                "task_id": task_id,
                "task_name": task_name,
                "agent_id": agent_id,
                "agent_name": agent_name,
            },
        ) as span:
            heartbeat_if_in_workflow("task cancel")

            # Extract headers from request; pass-through to agent
            extra_headers = request.get("headers") if request else None
            request_options: RequestOptions | None = {"additional_headers": extra_headers} if extra_headers else None

            task_response = await self._terminaluse_client.tasks.cancel(
                task_id,
                request_options=request_options,
            )

            # TaskResponse has the same fields as Task, so we can create a Task from it
            task_entry = Task(
                id=task_response.id,
                status=task_response.status,
                namespace_id=task_response.namespace_id,
                filesystem_id=task_response.filesystem_id,
                name=task_response.name,
                params=task_response.params,
                created_at=task_response.created_at,
                updated_at=task_response.updated_at,
            )
            if span:
                span.output = task_entry.model_dump()
            return task_entry
