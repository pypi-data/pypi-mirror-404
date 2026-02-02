"""Core Claude SDK integration utilities.

This module provides utilities for integrating with the Claude Agent SDK,
including delta accumulation for streaming and message type conversion.
"""

from terminaluse.lib.core.claude.delta_accumulator import (
    AccumulatorRegistry,
    ClaudeDeltaAccumulator,
)
from terminaluse.lib.core.claude.message_converter import (
    get_session_id,
    is_stream_event,
    is_claude_message,
    is_result_message,
    claude_message_to_content,
    blocks_to_platform_contents,
    claude_message_to_platform_contents,
)

__all__ = [
    "ClaudeDeltaAccumulator",
    "AccumulatorRegistry",
    "claude_message_to_content",
    "claude_message_to_platform_contents",
    "blocks_to_platform_contents",
    "is_claude_message",
    "is_stream_event",
    "is_result_message",
    "get_session_id",
]
