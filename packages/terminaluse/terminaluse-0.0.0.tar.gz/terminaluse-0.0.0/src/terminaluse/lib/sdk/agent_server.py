"""
AgentServer - Simplified API for creating TerminalUse agents.

This module provides a clean, simple interface for creating async agents
with optional Temporal support.

Example usage:

    # Basic async agent (no Temporal)
    from terminaluse.lib.sdk.agent_server import AgentServer

    server = AgentServer()

    @server.on_create
    async def handle_create(ctx: TaskContext, params: dict[str, Any]):
        await ctx.state.create(state={"initialized": True})

    @server.on_event
    async def handle_event(ctx: TaskContext, event: Event):
        await ctx.reply(f"Received: {event.content}")

    @server.on_cancel
    async def handle_cancel(ctx: TaskContext):
        await ctx.reply("Task cancelled")


    # Agent with Temporal workflows
    server = AgentServer(temporal=True)
    # Handlers are managed by Temporal workflow
"""

from __future__ import annotations

import os
from typing import Any

from terminaluse.lib.types.fastacp import AsyncACPConfig, TemporalACPConfig
from terminaluse.lib.sandbox.config import SandboxConfig
from terminaluse.lib.sdk.fastacp.fastacp import FastACP
from terminaluse.lib.sdk.fastacp.impl.temporal_acp import TemporalACP
from terminaluse.lib.sdk.fastacp.impl.async_base_acp import AsyncBaseACP


class AgentServer:
    """
    Simplified factory for creating TerminalUse agent servers.

    All agents are async by default. Use `temporal=True` to enable
    Temporal workflows for reliability and long-running tasks.

    Args:
        temporal: Enable Temporal workflows (default: False)
        temporal_address: Temporal server address (only used if temporal=True)
        plugins: Temporal client plugins (only used if temporal=True)
        interceptors: Temporal worker interceptors (only used if temporal=True)
        sandbox_config: Optional sandbox configuration for bubblewrap isolation

    Example:
        # Basic agent
        server = AgentServer()

        @server.on_event
        async def handle_event(ctx: TaskContext, event: Event):
            await ctx.reply(f"Received: {event.content}")

        # Agent with Temporal workflows
        server = AgentServer(temporal=True)

        # Agent with custom sandbox configuration
        from terminaluse.lib.sandbox.config import SandboxConfig
        server = AgentServer(sandbox_config=SandboxConfig(timeout_seconds=600))
    """

    def __init__(
        self,
        temporal: bool = False,
        temporal_address: str | None = None,
        plugins: list[Any] | None = None,
        interceptors: list[Any] | None = None,
        sandbox_config: SandboxConfig | None = None,
    ):
        """Create a new AgentServer instance."""
        self._temporal = temporal
        self._sandbox_config = sandbox_config

        if temporal:
            # Create Temporal-backed server
            config = TemporalACPConfig(
                type="temporal",
                temporal_address=temporal_address or os.getenv("TEMPORAL_ADDRESS", "localhost:7233"),
                plugins=plugins or [],
                interceptors=interceptors or [],
            )
            server = FastACP.create(
                acp_type="async",
                config=config,
                sandbox_config=sandbox_config,
            )
            self._server: AsyncBaseACP | TemporalACP = server  # type: ignore[assignment]
        else:
            # Create basic async server
            async_config = AsyncACPConfig(type="base")
            server = FastACP.create(
                acp_type="async",
                config=async_config,
                sandbox_config=sandbox_config,
            )
            self._server = server  # type: ignore[assignment]

    @property
    def on_create(self):
        """Decorator for handling task creation with TaskContext.

        The decorated function receives a TaskContext with pre-bound task/agent IDs
        and a params dict.

        Example:
            @server.on_create
            async def handle_create(ctx: TaskContext, params: dict[str, Any]):
                agent_type = params.get("agent_type")
                await ctx.state.create(state={"agent_type": agent_type})
                await ctx.reply("Task created!")
        """
        return self._server.on_create

    @property
    def on_event(self):
        """Decorator for handling incoming events with TaskContext.

        The decorated function receives a TaskContext with pre-bound task/agent IDs
        and the Event object.

        Example:
            @server.on_event
            async def handle_event(ctx: TaskContext, event: Event):
                await ctx.reply(f"Received: {event.content}")
        """
        return self._server.on_event

    @property
    def on_cancel(self):
        """Decorator for handling task cancellation with TaskContext.

        The decorated function receives a TaskContext with pre-bound task/agent IDs.

        Example:
            @server.on_cancel
            async def handle_cancel(ctx: TaskContext):
                await ctx.reply("Task cancelled")
        """
        return self._server.on_cancel

    # Expose the underlying ASGI app for uvicorn
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying server."""
        return getattr(self._server, name)

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        """ASGI interface - delegate to underlying server.

        This is needed because Python doesn't look up special methods
        like __call__ through __getattr__.
        """
        await self._server(scope, receive, send)
