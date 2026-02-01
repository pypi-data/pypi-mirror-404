from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, BaseModel

from terminaluse.types.task import Task
from terminaluse.types.agent import Agent
from terminaluse.types.event import Event


class RPCMethod(str, Enum):
    """Available JSON-RPC methods for agent communication."""

    EVENT_SEND = "event/send"
    TASK_CANCEL = "task/cancel"
    TASK_CREATE = "task/create"


class CreateTaskParams(BaseModel):
    """Parameters for task/create method.

    Attributes:
        agent: The agent that the task was sent to.
        task: The task to be created.
        params: The parameters for the task as inputted by the user.
        request: Additional request context including headers forwarded to this agent.
    """

    agent: Agent = Field(..., description="The agent that the task was sent to")
    task: Task = Field(..., description="The task to be created")
    params: dict[str, Any] | None = Field(
        None,
        description="The parameters for the task as inputted by the user",
    )
    request: dict[str, Any] | None = Field(
        default=None,
        description="Additional request context including headers forwarded to this agent",
    )


class SendEventParams(BaseModel):
    """Parameters for event/send method.

    Attributes:
        agent: The agent that the event was sent to.
        task: The task that the message was sent to.
        event: The event that was sent to the agent.
        request: Additional request context including headers forwarded to this agent.
    """

    agent: Agent = Field(..., description="The agent that the event was sent to")
    task: Task = Field(..., description="The task that the message was sent to")
    event: Event = Field(..., description="The event that was sent to the agent")
    request: dict[str, Any] | None = Field(
        default=None,
        description="Additional request context including headers forwarded to this agent",
    )


class CancelTaskParams(BaseModel):
    """Parameters for task/cancel method.

    Attributes:
        agent: The agent that the task was sent to.
        task: The task that was cancelled.
        request: Additional request context including headers forwarded to this agent.
    """

    agent: Agent = Field(..., description="The agent that the task was sent to")
    task: Task = Field(..., description="The task that was cancelled")
    request: dict[str, Any] | None = Field(
        default=None,
        description="Additional request context including headers forwarded to this agent",
    )


RPC_SYNC_METHODS: list[RPCMethod] = []

PARAMS_MODEL_BY_METHOD: dict[RPCMethod, type[BaseModel]] = {
    RPCMethod.EVENT_SEND: SendEventParams,
    RPCMethod.TASK_CANCEL: CancelTaskParams,
    RPCMethod.TASK_CREATE: CreateTaskParams,
}
