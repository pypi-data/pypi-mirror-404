# ruff: noqa: I001
# Import order matters - AsyncTracer must come after client import to avoid circular imports
from __future__ import annotations
from datetime import timedelta
from typing import Any

from temporalio.common import RetryPolicy

from terminaluse import AsyncTerminalUse  # noqa: F401
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client
from terminaluse.lib.core.services.adk.acp.acp import ACPService
from terminaluse.lib.core.services.adk.events import EventsService
from terminaluse.lib.core.temporal.activities.activity_helpers import ActivityHelpers
from terminaluse.lib.core.temporal.activities.adk.events_activities import (
    EventsActivityName,
    GetEventParams,
    ListEventsParams,
)
from terminaluse.lib.core.temporal.activities.adk.acp.acp_activities import (
    ACPActivityName,
    EventSendParams,
)
from terminaluse.lib.core.tracing.tracer import AsyncTracer
from terminaluse.types.event import Event
from terminaluse.types.task_message import TaskMessageContent
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import in_temporal_workflow

logger = make_logger(__name__)

# Default retry policy for all events operations
DEFAULT_RETRY_POLICY = RetryPolicy(maximum_attempts=1)


class EventsModule:
    """
    Module for managing events in TerminalUse.
    Provides high-level async methods for retrieving, listing, and sending events.
    """

    def __init__(
        self,
        events_service: EventsService | None = None,
        acp_service: ACPService | None = None,
    ):
        if events_service is None or acp_service is None:
            terminaluse_client = create_async_terminaluse_client()
            tracer = AsyncTracer(terminaluse_client)
            if events_service is None:
                self._events_service = EventsService(terminaluse_client=terminaluse_client, tracer=tracer)
            else:
                self._events_service = events_service
            if acp_service is None:
                self._acp_service = ACPService(terminaluse_client=terminaluse_client, tracer=tracer)
            else:
                self._acp_service = acp_service
        else:
            self._events_service = events_service
            self._acp_service = acp_service

    async def get(
        self,
        event_id: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> Event | None:
        """
        Get an event by ID.

        Args:
            event_id (str): The ID of the event.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            Optional[Event]: The event if found, None otherwise.
        """
        params = GetEventParams(
            event_id=event_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=EventsActivityName.GET_EVENT,
                request=params,
                response_type=Event,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._events_service.get_event(
                event_id=event_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    async def list(
        self,
        task_id: str,
        agent_id: str,
        last_processed_event_id: str | None = None,
        limit: int | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> list[Event]:
        """
        List events for a specific task and agent.

        Args:
            task_id (str): The ID of the task.
            agent_id (str): The ID of the agent.
            last_processed_event_id (Optional[str]): Optional event ID to get events after this ID.
            limit (Optional[int]): Optional limit on number of results.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            List[Event]: List of events ordered by sequence_id.
        """
        params = ListEventsParams(
            task_id=task_id,
            agent_id=agent_id,
            last_processed_event_id=last_processed_event_id,
            limit=limit,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=EventsActivityName.LIST_EVENTS,
                request=params,
                response_type=list[Event],
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._events_service.list(
                task_id=task_id,
                agent_id=agent_id,
                last_processed_event_id=last_processed_event_id,
                limit=limit,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    async def send(
        self,
        task_id: str,
        content: TaskMessageContent,
        agent_id: str | None = None,
        agent_name: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        request: dict[str, Any] | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> Event:
        """
        Send an event to a task.

        This triggers the on_event handler of the agent handling the task.

        Args:
            task_id (str): The ID of the task to send the event to.
            content (TaskMessageContent): The content of the event.
            agent_id (Optional[str]): The ID of the agent (optional if agent_name provided).
            agent_name (Optional[str]): The name of the agent (optional if agent_id provided).
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            request (Optional[dict]): Additional request context including headers to forward.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            Event: The created event.
        """
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=ACPActivityName.EVENT_SEND,
                request=EventSendParams(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    task_id=task_id,
                    content=content,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    request=request,
                ),
                response_type=Event,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._acp_service.event_send(
                task_id=task_id,
                content=content,
                agent_id=agent_id,
                agent_name=agent_name,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                request=request,
            )
