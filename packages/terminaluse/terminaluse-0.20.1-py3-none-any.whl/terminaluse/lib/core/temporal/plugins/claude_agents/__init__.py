"""Claude Agents SDK integration with Temporal.

This plugin provides integration between Claude Agents SDK and TerminalUse's
Temporal-based orchestration platform.

Features:
- Temporal activity wrapper for Claude SDK calls
- Real-time streaming to Redis/UI
- Session resume for conversation context
- Tool call visibility (Read, Write, Bash, etc.)
- Subagent support with nested tracing
- Filesystem isolation per task

Architecture:
- activities.py: Temporal activity definitions
- message_handler.py: Message parsing and streaming logic
- Uses ContextInterceptor for context threading

Usage:
    from terminaluse.lib.core.temporal.plugins.claude_agents import (
        run_claude_agent_activity,
        create_filesystem_directory,
        ContextInterceptor,
    )

    # In worker
    worker = TerminalUseWorker(
        task_queue=queue_name,
        interceptors=[ContextInterceptor()],
    )

    activities = get_all_activities()
    activities.extend([run_claude_agent_activity, create_filesystem_directory])

    await worker.run(activities=activities, workflow=YourWorkflow)
"""

from terminaluse.lib.core.temporal.plugins.claude_agents.hooks import (
    TemporalStreamingHooks,
    create_streaming_hooks,
)
from terminaluse.lib.core.temporal.plugins.claude_agents.activities import (
    run_claude_agent_activity,
    create_filesystem_directory,
)
from terminaluse.lib.core.temporal.plugins.claude_agents.message_handler import (
    ClaudeMessageHandler,
)

# Context threading for streaming
from terminaluse.lib.core.temporal.interceptors import (
    ContextInterceptor,
    streaming_task_id,
    streaming_trace_id,
    streaming_parent_span_id,
)

__all__ = [
    # Activities
    "run_claude_agent_activity",
    "create_filesystem_directory",
    # Message handling
    "ClaudeMessageHandler",
    # Hooks
    "create_streaming_hooks",
    "TemporalStreamingHooks",
    # Context threading (reused from OpenAI)
    "ContextInterceptor",
    "streaming_task_id",
    "streaming_trace_id",
    "streaming_parent_span_id",
]
