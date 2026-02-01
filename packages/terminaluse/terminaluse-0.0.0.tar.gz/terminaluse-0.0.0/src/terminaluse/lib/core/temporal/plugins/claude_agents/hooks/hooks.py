"""Claude SDK hooks for tracing subagent execution.

This module provides hook callbacks that integrate with Claude SDK's hooks system
for tracing nested subagent execution in TerminalUse.

NOTE: Tool streaming is now handled through adk.messages.send() which accepts
Claude SDK message types directly. The hooks here are ONLY for tracing purposes.

Usage:
    # Users should send messages directly via adk.messages:
    async for message in query(prompt="...", options=options):
        await adk.messages.send(task_id=task_id, content=message)

    # Hooks are optional and only needed for tracing subagent spans:
    hooks = create_tracing_hooks(task_id, trace_id, parent_span_id)
    options = ClaudeAgentOptions(hooks=hooks)
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import HookMatcher

from terminaluse.lib import adk
from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)


class TracingHooks:
    """Hooks for tracing subagent execution in TerminalUse.

    Creates nested trace spans when Claude executes subagent tools (Task tool).
    This allows tracking of subagent execution in the tracing system.

    NOTE: Tool requests/responses are now captured in ClaudeMessageContent
    via adk.messages.send(). These hooks are ONLY for tracing, not streaming.
    """

    def __init__(
        self,
        task_id: str | None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ):
        """Initialize tracing hooks.

        Args:
            task_id: TerminalUse task ID (for logging context)
            trace_id: Trace ID for nested spans
            parent_span_id: Parent span ID for subagent spans
        """
        self.task_id = task_id
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id

        # Track active subagent spans
        self.subagent_spans: dict[str, Any] = {}  # tool_call_id -> (ctx, span)

    async def pre_tool_use(
        self,
        input_data: dict[str, Any],
        tool_use_id: str | None,
        _context: Any,
    ) -> dict[str, Any]:
        """Hook called before tool execution.

        Creates a nested trace span for subagent tools (Task tool).

        Args:
            input_data: Contains tool_name, tool_input from Claude SDK
            tool_use_id: Unique ID for this tool call
            _context: Hook context from Claude SDK

        Returns:
            Empty dict (allow execution to proceed)
        """
        if not tool_use_id:
            return {}

        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        logger.debug(f"Tool started: {tool_name}")

        # Create nested trace span for subagent (Task) tools
        if tool_name == "Task" and self.trace_id and self.parent_span_id:
            subagent_type = tool_input.get("subagent_type", "unknown")
            logger.info(f"Subagent started: {subagent_type}")

            subagent_ctx = adk.tracing.span(
                trace_id=self.trace_id,
                parent_id=self.parent_span_id,
                name=f"Subagent: {subagent_type}",
                input=tool_input,
            )
            subagent_span = await subagent_ctx.__aenter__()
            self.subagent_spans[tool_use_id] = (subagent_ctx, subagent_span)

        return {}

    async def post_tool_use(
        self,
        input_data: dict[str, Any],
        tool_use_id: str | None,
        _context: Any,
    ) -> dict[str, Any]:
        """Hook called after tool execution.

        Closes the nested trace span for subagent tools.

        Args:
            input_data: Contains tool_name, tool_output from Claude SDK
            tool_use_id: Unique ID for this tool call
            _context: Hook context from Claude SDK

        Returns:
            Empty dict
        """
        if not tool_use_id:
            return {}

        tool_name = input_data.get("tool_name", "unknown")
        tool_output = input_data.get("tool_output", "")

        logger.debug(f"Tool completed: {tool_name}")

        # Close subagent span if this was a Task tool
        if tool_use_id in self.subagent_spans:
            subagent_ctx, subagent_span = self.subagent_spans[tool_use_id]
            subagent_span.output = {"result": tool_output}
            await subagent_ctx.__aexit__(None, None, None)
            logger.info(f"Subagent completed: {tool_name}")
            del self.subagent_spans[tool_use_id]

        return {}


def create_tracing_hooks(
    task_id: str | None = None,
    trace_id: str | None = None,
    parent_span_id: str | None = None,
) -> dict[str, list[HookMatcher]]:
    """Create Claude SDK hooks for tracing subagent execution.

    These hooks are OPTIONAL and only needed if you want to trace subagent
    execution. Tool requests/responses are captured via adk.messages.send().

    Args:
        task_id: TerminalUse task ID (for logging context)
        trace_id: Trace ID for nested spans
        parent_span_id: Parent span ID for subagent spans

    Returns:
        Dict with PreToolUse and PostToolUse hook configurations

    Example:
        hooks = create_tracing_hooks(task_id, trace_id, parent_span_id)
        options = ClaudeAgentOptions(hooks=hooks)

        async for message in query(prompt="...", options=options):
            await adk.messages.send(task_id=task_id, content=message)
    """
    hooks_instance = TracingHooks(task_id, trace_id, parent_span_id)

    return {
        "PreToolUse": [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[hooks_instance.pre_tool_use],  # type: ignore[list-item]
            )
        ],
        "PostToolUse": [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[hooks_instance.post_tool_use],  # type: ignore[list-item]
            )
        ],
    }


# Backwards compatibility alias
create_streaming_hooks = create_tracing_hooks
TemporalStreamingHooks = TracingHooks
