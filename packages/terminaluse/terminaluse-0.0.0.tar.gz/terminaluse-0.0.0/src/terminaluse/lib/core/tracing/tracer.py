from __future__ import annotations

from terminaluse import TerminalUse, AsyncTerminalUse
from terminaluse.lib.core.tracing.trace import Trace, AsyncTrace
from terminaluse.lib.core.tracing.tracing_processor_manager import (
    get_sync_tracing_processors,
    get_async_tracing_processors,
)


class Tracer:
    """
    Tracer is the main entry point for tracing in TerminalUse.
    It manages the client connection and creates traces.
    """

    def __init__(self, client: TerminalUse):
        """
        Initialize a new sync tracer with the provided client.

        Args:
            client: TerminalUse client instance used for API communication.
        """
        self.client = client

    def trace(self, trace_id: str | None = None, task_id: str | None = None) -> Trace:
        """
        Create a new trace with the given trace ID.

        Args:
            trace_id: The trace ID to use.
            task_id: The task ID to associate with spans.

        Returns:
            A new Trace instance.
        """
        return Trace(
            processors=get_sync_tracing_processors(),
            client=self.client,
            trace_id=trace_id,
            task_id=task_id,
        )


class AsyncTracer:
    """
    AsyncTracer is the async version of Tracer.
    It manages the async client connection and creates async traces.
    """

    def __init__(self, client: AsyncTerminalUse):
        """
        Initialize a new async tracer with the provided client.

        Args:
            client: AsyncTerminalUse client instance used for API communication.
        """
        self.client = client

    def trace(self, trace_id: str | None = None, task_id: str | None = None) -> AsyncTrace:
        """
        Create a new trace with the given trace ID.

        Args:
            trace_id: The trace ID to use.
            task_id: The task ID to associate with spans.

        Returns:
            A new AsyncTrace instance.
        """
        return AsyncTrace(
            processors=get_async_tracing_processors(),
            client=self.client,
            trace_id=trace_id,
            task_id=task_id,
        )
