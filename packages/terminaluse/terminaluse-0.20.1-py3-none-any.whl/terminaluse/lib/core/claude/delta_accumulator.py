"""Delta accumulator for Claude SDK streaming events."""

from __future__ import annotations

import json
import threading
from typing import Any
from dataclasses import field, dataclass

from terminaluse.types.task_message_delta import (
    TaskMessageDelta,
    TaskMessageDelta_Text,
    TaskMessageDelta_ToolRequest,
    TaskMessageDelta_ReasoningContent,
)


@dataclass
class ContentBlockState:
    """State for a content block being accumulated."""

    block_type: str
    index: int
    text: str = ""
    tool_id: str = ""
    tool_name: str = ""
    tool_input_json: str = ""
    thinking: str = ""
    thinking_signature: str = ""


@dataclass
class AccumulatedMessage:
    """Accumulated message data from streaming events."""

    message_id: str = ""
    model: str = ""
    role: str = "assistant"
    content_blocks: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "assistant",
            "message": {
                "id": self.message_id,
                "type": "message",
                "role": self.role,
                "model": self.model,
                "content": self.content_blocks,
                "stop_reason": self.stop_reason,
                "stop_sequence": self.stop_sequence,
                "usage": self.usage,
            },
        }


class ClaudeDeltaAccumulator:
    """Accumulates StreamEvent deltas into complete Claude messages."""

    def __init__(self):
        self._message = AccumulatedMessage()
        self._current_block: ContentBlockState | None = None
        self._is_complete: bool = False

    def process_event(self, event: Any) -> TaskMessageDelta | None:
        """Process a streaming event, returning a delta if there's content to stream."""
        raw_event = event.event if hasattr(event, "event") else event
        event_type = raw_event.get("type", "")
        handler = getattr(self, f"_handle_{event_type}", None)
        return handler(raw_event) if handler else None

    def _handle_message_start(self, event: dict[str, Any]) -> None:
        # Reset state for new message to prevent duplicate content from previous turns
        self._is_complete = False
        self._message = AccumulatedMessage()
        self._current_block = None

        message = event.get("message", {})
        self._message.message_id = message.get("id", "")
        self._message.model = message.get("model", "")
        self._message.role = message.get("role", "assistant")
        self._message.usage = message.get("usage", {})

    def _handle_content_block_start(self, event: dict[str, Any]) -> TaskMessageDelta | None:
        content_block = event.get("content_block", {})
        block_type = content_block.get("type", "text")

        self._current_block = ContentBlockState(
            block_type=block_type,
            index=event.get("index", 0),
        )

        if block_type == "tool_use":
            self._current_block.tool_id = content_block.get("id", "")
            self._current_block.tool_name = content_block.get("name", "")
            return TaskMessageDelta_ToolRequest(
                tool_call_id=self._current_block.tool_id,
                name=self._current_block.tool_name,
                arguments_delta="",
            )
        return None

    def _handle_content_block_delta(self, event: dict[str, Any]) -> TaskMessageDelta | None:
        if not self._current_block:
            return None

        delta = event.get("delta", {})
        delta_type = delta.get("type", "")

        if delta_type == "text_delta":
            text = delta.get("text", "")
            self._current_block.text += text
            return TaskMessageDelta_Text(text_delta=text)

        if delta_type == "input_json_delta":
            partial_json = delta.get("partial_json", "")
            self._current_block.tool_input_json += partial_json
            return TaskMessageDelta_ToolRequest(
                tool_call_id=self._current_block.tool_id,
                name=self._current_block.tool_name,
                arguments_delta=partial_json,
            )

        if delta_type == "thinking_delta":
            thinking = delta.get("thinking", "")
            self._current_block.thinking += thinking
            return TaskMessageDelta_ReasoningContent(
                content_index=self._current_block.index,
                content_delta=thinking,
            )

        if delta_type == "signature_delta":
            self._current_block.thinking_signature += delta.get("signature", "")

        return None

    def _handle_content_block_stop(self, _event: dict[str, Any]) -> None:
        if not self._current_block:
            return

        block = self._current_block
        if block.block_type == "text":
            self._message.content_blocks.append({"type": "text", "text": block.text})
        elif block.block_type == "tool_use":
            try:
                tool_input = json.loads(block.tool_input_json) if block.tool_input_json else {}
            except json.JSONDecodeError:
                tool_input = {}
            self._message.content_blocks.append(
                {
                    "type": "tool_use",
                    "id": block.tool_id,
                    "name": block.tool_name,
                    "input": tool_input,
                }
            )
        elif block.block_type == "thinking":
            self._message.content_blocks.append(
                {
                    "type": "thinking",
                    "thinking": block.thinking,
                    "signature": block.thinking_signature,
                }
            )
        self._current_block = None

    def _handle_message_delta(self, event: dict[str, Any]) -> None:
        delta = event.get("delta", {})
        if "stop_reason" in delta:
            self._message.stop_reason = delta["stop_reason"]
        if "stop_sequence" in delta:
            self._message.stop_sequence = delta["stop_sequence"]
        if usage := event.get("usage"):
            self._message.usage.update(usage)

    def _handle_message_stop(self, _event: dict[str, Any]) -> None:
        self._is_complete = True

    def is_complete(self) -> bool:
        return self._is_complete

    def build_message_dict(self) -> dict[str, Any]:
        return self._message.to_dict()

    def get_content_blocks(self) -> list[dict[str, Any]]:
        return self._message.content_blocks.copy()


# Module-level accumulator registry
_accumulators: dict[tuple[str, str], ClaudeDeltaAccumulator] = {}
_accumulators_lock = threading.Lock()


class AccumulatorRegistry:
    """Thread-safe registry for accumulator instances per (task_id, session_id)."""

    @staticmethod
    def get_instance() -> AccumulatorRegistry:
        return AccumulatorRegistry()

    def get_or_create(self, task_id: str, session_id: str) -> ClaudeDeltaAccumulator:
        key = (task_id, session_id)
        with _accumulators_lock:
            if key not in _accumulators:
                _accumulators[key] = ClaudeDeltaAccumulator()
            return _accumulators[key]

    def cleanup(self, task_id: str, session_id: str) -> None:
        with _accumulators_lock:
            _accumulators.pop((task_id, session_id), None)

    def has_active_session(self, task_id: str) -> bool:
        with _accumulators_lock:
            return any(k[0] == task_id for k in _accumulators)
