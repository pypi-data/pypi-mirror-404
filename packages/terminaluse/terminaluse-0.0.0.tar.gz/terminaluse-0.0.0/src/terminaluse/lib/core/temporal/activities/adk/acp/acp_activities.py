from __future__ import annotations

from enum import Enum
from typing import Any

from temporalio import activity

from terminaluse.types.task import Task
from terminaluse.types.event import Event
from terminaluse.lib.types.tracing import BaseModelWithTraceParams
from terminaluse.lib.utils.logging import make_logger
from terminaluse.types.task_message_content import TaskMessageContent
from terminaluse.lib.core.services.adk.acp.acp import ACPService

logger = make_logger(__name__)


class ACPActivityName(str, Enum):
    TASK_CREATE = "task-create"
    EVENT_SEND = "event-send"
    TASK_CANCEL = "task-cancel"


class TaskCreateParams(BaseModelWithTraceParams):
    name: str | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    params: dict[str, Any] | None = None
    request: dict[str, Any] | None = None


class EventSendParams(BaseModelWithTraceParams):
    agent_id: str | None = None
    agent_name: str | None = None
    task_id: str | None = None
    content: TaskMessageContent
    request: dict[str, Any] | None = None


class TaskCancelParams(BaseModelWithTraceParams):
    task_id: str | None = None
    task_name: str | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    request: dict[str, Any] | None = None


class ACPActivities:
    def __init__(self, acp_service: ACPService):
        self._acp_service = acp_service

    @activity.defn(name=ACPActivityName.TASK_CREATE)
    async def task_create(self, params: TaskCreateParams) -> Task:
        return await self._acp_service.task_create(
            name=params.name,
            agent_id=params.agent_id,
            agent_name=params.agent_name,
            params=params.params,
            trace_id=params.trace_id,
            parent_span_id=params.parent_span_id,
            request=params.request,
        )

    @activity.defn(name=ACPActivityName.EVENT_SEND)
    async def event_send(self, params: EventSendParams) -> Event:
        return await self._acp_service.event_send(
            agent_id=params.agent_id,
            agent_name=params.agent_name,
            task_id=params.task_id,
            content=params.content,
            trace_id=params.trace_id,
            parent_span_id=params.parent_span_id,
            request=params.request,
        )

    @activity.defn(name=ACPActivityName.TASK_CANCEL)
    async def task_cancel(self, params: TaskCancelParams) -> Task:
        return await self._acp_service.task_cancel(
            task_id=params.task_id,
            task_name=params.task_name,
            agent_id=params.agent_id,
            agent_name=params.agent_name,
            trace_id=params.trace_id,
            parent_span_id=params.parent_span_id,
            request=params.request,
        )
