from __future__ import annotations

from terminaluse import AsyncTerminalUse
from terminaluse.types.event import Event
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.core.tracing.tracer import AsyncTracer

logger = make_logger(__name__)


class EventsService:
    def __init__(self, terminaluse_client: AsyncTerminalUse, tracer: AsyncTracer):
        self._terminaluse_client = terminaluse_client
        self._tracer = tracer

    async def get_event(
        self,
        event_id: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Event | None:
        trace = self._tracer.trace(trace_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="get_event",
            input={"event_id": event_id},
        ) as span:
            event = await self._terminaluse_client.events.retrieve(event_id=event_id)
            if span:
                span.output = event.model_dump()
            return event

    async def list(
        self,
        task_id: str,
        agent_id: str,
        last_processed_event_id: str | None = None,
        limit: int | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> list[Event]:
        trace = self._tracer.trace(trace_id, task_id=task_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="events.list",
            input={
                "task_id": task_id,
                "agent_id": agent_id,
                "last_processed_event_id": last_processed_event_id,
                "limit": limit,
            },
        ) as span:
            events = await self._terminaluse_client.events.list(
                task_id=task_id,
                agent_id=agent_id,
                last_processed_event_id=last_processed_event_id,
                limit=limit,
            )
            if span:
                span.output = {"events": [event.model_dump() for event in events]}
            return events
