from __future__ import annotations

from typing import Any, Callable, AsyncGenerator, override
from contextlib import asynccontextmanager

from fastapi import FastAPI

from terminaluse.types.event import Event
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.types.task_context import TaskContext
from terminaluse.lib.environment_variables import EnvironmentVariables
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer
from terminaluse.lib.core.clients.temporal.temporal_client import TemporalClient
from terminaluse.lib.core.temporal.services.temporal_task_service import TemporalTaskService

logger = make_logger(__name__)


class TemporalACP(BaseACPServer):
    """
    Temporal-specific implementation of AsyncAgentACP.
    Uses TaskService to forward operations to temporal workflows.
    """

    def __init__(
        self,
        temporal_address: str,
        temporal_task_service: TemporalTaskService | None = None,
        plugins: list[Any] | None = None,
        interceptors: list[Any] | None = None,
    ):
        super().__init__()
        self._temporal_task_service = temporal_task_service
        self._temporal_address = temporal_address
        self._plugins = plugins or []
        self._interceptors = interceptors or []

    @classmethod
    @override
    def create(  # type: ignore[override]
        cls, temporal_address: str, plugins: list[Any] | None = None, interceptors: list[Any] | None = None
    ) -> "TemporalACP":
        logger.info("Initializing TemporalACP instance")

        # Create instance without temporal client initially
        temporal_acp = cls(temporal_address=temporal_address, plugins=plugins, interceptors=interceptors)
        temporal_acp._setup_handlers()
        logger.info("TemporalACP instance initialized now")
        return temporal_acp

    @override
    def get_lifespan_function(self) -> Callable[[FastAPI], AsyncGenerator[None, None]]:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Create temporal client during startup
            if self._temporal_address is None:
                raise ValueError("Temporal address is not set")

            if self._temporal_task_service is None:
                env_vars = EnvironmentVariables.refresh()
                temporal_client = await TemporalClient.create(
                    temporal_address=self._temporal_address, plugins=self._plugins
                )
                self._temporal_task_service = TemporalTaskService(
                    temporal_client=temporal_client,
                    env_vars=env_vars,
                )

            # Call parent lifespan for agent registration
            async with super().get_lifespan_function()(app):  # type: ignore[misc]
                yield

        return lifespan  # type: ignore[return-value]

    @override
    def _setup_handlers(self):
        """Set up the handlers for temporal workflow operations"""

        @self.on_create
        async def handle_create(ctx: TaskContext, params: dict[str, Any]) -> None:
            """Default create task handler - logs the task"""
            logger.info(f"TemporalACP received task create rpc call for task {ctx.task.id}")
            if self._temporal_task_service is not None:
                await self._temporal_task_service.submit_task(
                    agent=ctx.agent, task=ctx.task, params=params
                )

        @self.on_event
        async def handle_event(ctx: TaskContext, event: Event) -> None:
            """Forward messages to running workflows via TaskService"""
            try:
                if self._temporal_task_service is not None:
                    await self._temporal_task_service.send_event(
                        agent=ctx.agent,
                        task=ctx.task,
                        event=event,
                        request=ctx.request,
                    )

            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                raise

        @self.on_cancel
        async def handle_cancel(ctx: TaskContext) -> None:
            """Cancel running workflows via TaskService"""
            try:
                if self._temporal_task_service is not None:
                    await self._temporal_task_service.cancel(task_id=ctx.task.id)
            except Exception as e:
                logger.error(f"Failed to cancel task: {e}")
                raise
