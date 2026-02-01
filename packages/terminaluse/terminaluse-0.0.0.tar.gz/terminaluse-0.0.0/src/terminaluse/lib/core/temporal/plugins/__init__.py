"""Temporal Plugins with Streaming Support.

This module provides streaming capabilities for Temporal workflows
using interceptors to thread task_id through workflows to activities.

The streaming implementation works by:
1. Using Temporal interceptors to thread task_id through the execution
2. Streaming LLM responses to Redis in real-time from activities
3. Returning complete responses to maintain Temporal determinism

Example:
    >>> from terminaluse.lib.core.temporal.interceptors import ContextInterceptor
    >>>
    >>> # Register interceptor with worker
    >>> interceptor = ContextInterceptor()
    >>> # Add interceptor to worker configuration
"""

from terminaluse.lib.core.temporal.interceptors import (
    ContextInterceptor,
    streaming_task_id,
    streaming_trace_id,
    streaming_parent_span_id,
)

__all__ = [
    "ContextInterceptor",
    "streaming_task_id",
    "streaming_trace_id",
    "streaming_parent_span_id",
]
