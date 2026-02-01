# ruff: noqa: I001
# Import order matters - AsyncTracer must come after client import to avoid circular imports
from __future__ import annotations
from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from temporalio.common import RetryPolicy

from terminaluse import AsyncTerminalUse  # noqa: F401
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client
from terminaluse.lib.core.services.adk.state import StateService
from terminaluse.lib.core.temporal.activities.activity_helpers import ActivityHelpers
from terminaluse.lib.core.temporal.activities.adk.state_activities import (
    CreateStateParams,
    DeleteStateParams,
    GetStateParams,
    StateActivityName,
    UpdateStateParams,
)
from terminaluse.lib.core.tracing.tracer import AsyncTracer
from terminaluse.types.state import State
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import in_temporal_workflow

logger = make_logger(__name__)

# Default retry policy for all state operations
DEFAULT_RETRY_POLICY = RetryPolicy(maximum_attempts=1)


class StateModule:
    """
    Module for managing task state in TerminalUse.
    Provides high-level async methods for creating, retrieving, updating, and deleting state.
    """

    def __init__(
        self,
        state_service: StateService | None = None,
    ):
        if state_service is None:
            terminaluse_client = create_async_terminaluse_client()
            tracer = AsyncTracer(terminaluse_client)
            self._state_service = StateService(terminaluse_client=terminaluse_client, tracer=tracer)
        else:
            self._state_service = state_service

    async def create(
        self,
        task_id: str,
        agent_id: str,
        state: dict[str, Any] | BaseModel,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> State:
        """
        Create a new state for a task and agent.

        Args:
            task_id (str): The ID of the task.
            agent_id (str): The ID of the agent.
            state (Dict[str, Any]): The state to create.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            State: The created state.
        """
        state_dict = state.model_dump() if isinstance(state, BaseModel) else state
        params = CreateStateParams(
            task_id=task_id,
            agent_id=agent_id,
            state=state_dict,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=StateActivityName.CREATE_STATE,
                request=params,
                response_type=State,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._state_service.create_state(
                task_id=task_id,
                agent_id=agent_id,
                state=state_dict,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    async def get(
        self,
        *,
        state_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> State | None:
        """
        Get a state by ID or by task and agent.

        Must provide either `state_id` OR both `task_id` and `agent_id`.

        Args:
            state_id (str): The ID of the state.
            task_id (str): The ID of the task.
            agent_id (str): The ID of the agent.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            Optional[State]: The state if found, None otherwise.

        Raises:
            ValueError: If neither state_id nor (task_id and agent_id) are provided.
        """
        if state_id is None and (task_id is None or agent_id is None):
            raise ValueError("Must provide either state_id or both task_id and agent_id")

        params = GetStateParams(
            state_id=state_id,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=StateActivityName.GET_STATE,
                request=params,
                response_type=State,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._state_service.get(
                state_id=state_id,
                task_id=task_id,
                agent_id=agent_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    async def update(
        self,
        state: dict[str, Any] | BaseModel,
        *,
        state_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> State:
        """
        Update a state.

        Must provide either `state_id` OR both `task_id` and `agent_id`.

        Args:
            state (Dict[str, Any]): The state to update.
            state_id (str): The ID of the state.
            task_id (str): The ID of the task.
            agent_id (str): The ID of the agent.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            State: The updated state.

        Raises:
            ValueError: If neither state_id nor (task_id and agent_id) are provided.
            ValueError: If state not found when using task_id and agent_id.
        """
        if state_id is None and (task_id is None or agent_id is None):
            raise ValueError("Must provide either state_id or both task_id and agent_id")

        # If no state_id provided, look it up
        if state_id is None:
            existing = await self.get(
                task_id=task_id,
                agent_id=agent_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                start_to_close_timeout=start_to_close_timeout,
                heartbeat_timeout=heartbeat_timeout,
                retry_policy=retry_policy,
            )
            if existing is None:
                raise ValueError(f"State not found for task_id={task_id}, agent_id={agent_id}")
            state_id = existing.id
            task_id = existing.task_id
            agent_id = existing.agent_id

        state_dict = state.model_dump() if isinstance(state, BaseModel) else state
        params = UpdateStateParams(
            state_id=state_id,
            task_id=task_id,
            agent_id=agent_id,
            state=state_dict,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=StateActivityName.UPDATE_STATE,
                request=params,
                response_type=State,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            # task_id and agent_id are guaranteed non-None:
            # - Either they were provided originally
            # - Or they were populated from existing.task_id/agent_id above
            assert task_id is not None, "task_id required for direct service update"
            assert agent_id is not None, "agent_id required for direct service update"
            return await self._state_service.update(
                state_id=state_id,
                task_id=task_id,
                agent_id=agent_id,
                state=state_dict,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    async def delete(
        self,
        state_id: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        start_to_close_timeout: timedelta = timedelta(seconds=5),
        heartbeat_timeout: timedelta = timedelta(seconds=5),
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> State:
        """
        Delete a state by ID.

        Args:
            state_id (str): The ID of the state.
            trace_id (Optional[str]): The trace ID for tracing.
            parent_span_id (Optional[str]): The parent span ID for tracing.
            start_to_close_timeout (timedelta): The start to close timeout.
            heartbeat_timeout (timedelta): The heartbeat timeout.
            retry_policy (RetryPolicy): The retry policy.

        Returns:
            State: The deleted state.
        """
        params = DeleteStateParams(
            state_id=state_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        if in_temporal_workflow():
            return await ActivityHelpers.execute_activity(
                activity_name=StateActivityName.DELETE_STATE,
                request=params,
                response_type=State,
                start_to_close_timeout=start_to_close_timeout,
                retry_policy=retry_policy,
                heartbeat_timeout=heartbeat_timeout,
            )
        else:
            return await self._state_service.delete_state(
                state_id=state_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )
