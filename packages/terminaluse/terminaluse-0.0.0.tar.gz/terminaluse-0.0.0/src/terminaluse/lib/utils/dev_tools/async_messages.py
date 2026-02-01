"""
Development utility for subscribing to async task messages with streaming support.

This module provides utilities to read existing messages from a task and subscribe
to new streaming messages, handling mid-stream connections gracefully.
"""

from __future__ import annotations

import re
import json
from typing import List, Optional
from datetime import datetime, timezone
from dataclasses import field, dataclass

from yaspin import yaspin  # type: ignore[import-untyped]
from rich.panel import Panel
from yaspin.core import Yaspin  # type: ignore[import-untyped]
from rich.console import Console
from rich.markdown import Markdown

from terminaluse import TerminalUse
from terminaluse.types import Task, TaskMessage, TaskResponse
from terminaluse.types.task_message_content import (
    TaskMessageContent_Reasoning,
    TaskMessageContent_Text,
    TaskMessageContent_ToolRequest,
    TaskMessageContent_ToolResponse,
)
from terminaluse.types.task_message_delta import (
    TaskMessageDelta_Text,
    TaskMessageDelta_ToolRequest,
    TaskMessageDelta_ToolResponse,
    TaskMessageDelta_ReasoningContent,
)
from terminaluse.types.task_stream_event import (
    TaskStreamEvent,
    TaskStreamEvent_Connected,
    TaskStreamEvent_Delta,
    TaskStreamEvent_Done,
    TaskStreamEvent_Error,
    TaskStreamEvent_Full,
    TaskStreamEvent_Start,
    TaskStreamEvent_TaskUpdated,
)

# =============================================================================
# State classes for stream_task_events
# =============================================================================


@dataclass
class ToolCallBuffer:
    """Buffer for accumulating tool call data during streaming."""

    tool_call_id: str
    name: str
    arguments_buffer: str = ""
    response_buffer: str = ""  # For streaming tool response content
    request_complete: bool = False  # Set True on done event
    request_printed: bool = False
    response_printed: bool = False


@dataclass
class MessageStreamState:
    """State for tracking a single message during streaming."""

    index: int
    is_done: bool = False
    text_buffer: str = ""  # For buffering when can't display yet
    reasoning_buffers: dict[int, str] = field(default_factory=dict)  # content_index -> text
    tool_calls: dict[str, ToolCallBuffer] = field(default_factory=dict)


def print_task_message(
    message: TaskMessage,
    print_messages: bool = True,
    rich_print: bool = True,
) -> None:
    """
    Print a task message in a formatted way.

    Args:
        message: The task message to print
        print_messages: Whether to actually print the message (for debugging)
        rich_print: Whether to use rich to print the message
    """
    if not print_messages:
        return

    # Skip empty messages
    if isinstance(message.content, TaskMessageContent_Text) and not message.content.content.strip():
        return

    # Skip empty reasoning messages
    if isinstance(message.content, TaskMessageContent_Reasoning):
        has_summary = bool(message.content.summary) and any(s for s in message.content.summary if s)
        has_content = (
            bool(message.content.content) and any(c for c in message.content.content if c)
            if message.content.content is not None
            else False
        )
        if not has_summary and not has_content:
            return

    timestamp = message.created_at.strftime("%m/%d/%Y %H:%M:%S") if message.created_at else "N/A"

    console = None
    if rich_print:
        console = Console(width=80)  # Fit better in Jupyter cells

    if isinstance(message.content, TaskMessageContent_Text):
        content = message.content.content
        content_type = "text"
    elif isinstance(message.content, TaskMessageContent_ToolRequest):
        tool_name = message.content.name
        tool_args = message.content.arguments

        # Format arguments as pretty JSON
        try:
            if isinstance(tool_args, str):
                parsed_args = json.loads(tool_args)
                formatted_args = json.dumps(parsed_args, indent=2)
            else:
                formatted_args = json.dumps(tool_args, indent=2)
            content = f"🔧 **Tool Request: {tool_name}**\n\n**Arguments:**\n```json\n{formatted_args}\n```"
        except (json.JSONDecodeError, TypeError):
            content = f"🔧 **Tool Request: {tool_name}**\n\n**Arguments:**\n```json\n{tool_args}\n```"

        content_type = "tool_request"
    elif isinstance(message.content, TaskMessageContent_ToolResponse):
        tool_name = message.content.name
        tool_response = message.content.content

        # Try to parse and format JSON response nicely
        try:
            if isinstance(tool_response, str):
                parsed_response = json.loads(tool_response)
                formatted_json = json.dumps(parsed_response, indent=2)
                content = f"✅ **Tool Response: {tool_name}**\n\n**Response:**\n```json\n{formatted_json}\n```"
            else:
                formatted_json = json.dumps(tool_response, indent=2)
                content = f"✅ **Tool Response: {tool_name}**\n\n**Response:**\n```json\n{formatted_json}\n```"
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, display as text
            if isinstance(tool_response, str):
                # Try to extract text content if it's a JSON string with text field
                try:
                    parsed = json.loads(tool_response)
                    if isinstance(parsed, dict) and "text" in parsed:
                        text_content = str(parsed["text"])
                        content = f"✅ **Tool Response: {tool_name}**\n\n{text_content}"
                    else:
                        content = f"✅ **Tool Response: {tool_name}**\n\n{tool_response}"
                except json.JSONDecodeError:
                    content = f"✅ **Tool Response: {tool_name}**\n\n{tool_response}"
            else:
                content = f"✅ **Tool Response: {tool_name}**\n\n{tool_response}"

        content_type = "tool_response"
    elif isinstance(message.content, TaskMessageContent_Reasoning):
        # Format reasoning content
        reasoning_parts = []

        # Add summary if available
        if message.content.summary:
            # Join summaries with double newline for better formatting
            summary_text = "\n\n".join(s for s in message.content.summary if s)
            if summary_text:
                reasoning_parts.append(summary_text)

        # Add full reasoning content if available
        if message.content.content:
            content_text = "\n\n".join(c for c in message.content.content if c)
            if content_text:
                reasoning_parts.append(content_text)

        # Format reasoning content (we already checked it's not empty at the top)
        content = "🧠 **Reasoning**\n\n" + "\n\n".join(reasoning_parts)
        content_type = "reasoning"
    else:
        content = f"{type(message.content).__name__}: {message.content}"
        content_type = "other"

    if rich_print and console:
        author_color = "bright_cyan" if message.content.author == "user" else "green"

        # Use different border styles and colors for different content types
        if content_type == "tool_request":
            border_style = "yellow"
        elif content_type == "tool_response":
            border_style = "bright_green"
        elif content_type == "reasoning":
            border_style = "bright_magenta"
            author_color = "bright_magenta"  # Also make the author text magenta
        else:
            border_style = author_color

        title = f"[bold {author_color}]{message.content.author.upper()}[/bold {author_color}] [{timestamp}]"
        panel = Panel(Markdown(content), title=title, border_style=border_style, width=80)
        console.print(panel)
    else:
        title = f"{message.content.author.upper()} [{timestamp}]"
        if content_type == "reasoning":
            title = f"🧠 REASONING [{timestamp}]"
        print(f"{title}\n{content}\n")


def print_task_message_update(
    task_message_update: TaskStreamEvent,
    print_messages: bool = True,
    rich_print: bool = True,
    show_deltas: bool = True,
) -> None:
    """
    Print a task stream event in a formatted way.

    This function handles different types of TaskStreamEvent objects:
    - TaskStreamEvent_Start: Shows start indicator
    - TaskStreamEvent_Delta: Shows deltas in real-time (if show_deltas=True)
    - TaskStreamEvent_Full: Shows complete message content
    - TaskStreamEvent_Done: Shows completion indicator

    Args:
        task_message_update: The TaskStreamEvent object to print
        print_messages: Whether to actually print the message (for debugging)
        rich_print: Whether to use rich formatting
        show_deltas: Whether to show delta updates in real-time
    """
    if not print_messages:
        return

    console = None
    if rich_print:
        console = Console(width=80)

    if isinstance(task_message_update, TaskStreamEvent_Start):
        if rich_print and console:
            console.print("🚀 [cyan]Agent started responding...[/cyan]")
        else:
            print("🚀 Agent started responding...")

    elif isinstance(task_message_update, TaskStreamEvent_Delta):
        if show_deltas and task_message_update.delta:
            if isinstance(task_message_update.delta, TaskMessageDelta_Text):
                print(task_message_update.delta.text_delta, end="", flush=True)
            elif rich_print and console:
                console.print(f"[yellow]Non-text delta: {type(task_message_update.delta).__name__}[/yellow]")
            else:
                print(f"Non-text delta: {type(task_message_update.delta).__name__}")

    elif isinstance(task_message_update, TaskStreamEvent_Full):
        if isinstance(task_message_update.content, TaskMessageContent_Text):
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

            if rich_print and console:
                author_color = "bright_cyan" if task_message_update.content.author == "user" else "green"
                title = f"[bold {author_color}]{task_message_update.content.author.upper()}[/bold {author_color}] [{timestamp}]"
                panel = Panel(
                    Markdown(task_message_update.content.content), title=title, border_style=author_color, width=80
                )
                console.print(panel)
            else:
                title = f"{task_message_update.content.author.upper()} [{timestamp}]"
                print(f"\n{title}\n{task_message_update.content.content}\n")
        else:
            content_type = type(task_message_update.content).__name__
            if rich_print and console:
                console.print(f"[yellow]Non-text content: {content_type}[/yellow]")
            else:
                print(f"Non-text content: {content_type}")

    elif isinstance(task_message_update, TaskStreamEvent_Done):
        if rich_print and console:
            console.print("\n✅ [green]Agent finished responding.[/green]")
        else:
            print("\n✅ Agent finished responding.")

    elif isinstance(task_message_update, TaskStreamEvent_Error):
        error_msg = task_message_update.message
        if rich_print and console:
            console.print(f"\n❌ [red]Error: {error_msg}[/red]")
        else:
            print(f"\n❌ Error: {error_msg}")

    # TaskStreamEvent_Connected and TaskStreamEvent_TaskUpdated are handled silently
    # as they are informational events that don't require user-facing output


def subscribe_to_async_task_messages(
    client: TerminalUse,
    task: Task,
    only_after_timestamp: Optional[datetime] = None,
    print_messages: bool = True,
    rich_print: bool = True,
    timeout: int = 10,
) -> List[TaskMessage]:
    """
    Subscribe to async task messages and collect completed messages.

    This function:
    1. Reads all existing messages from the task
    2. Optionally filters messages after a timestamp
    3. Shows a loading message while listening
    4. Subscribes to task message events
    5. Fetches and displays complete messages when they finish
    6. Returns all messages collected during the session

    Features:
    - Uses Rich library for beautiful formatting in Jupyter notebooks
    - Agent messages are formatted as Markdown
    - User and agent messages are displayed in colored panels with fixed width
    - Optimized for Jupyter notebook display

    Args:
        client: The TerminalUse client instance
        task: The task to subscribe to
        print_messages: Whether to print messages as they arrive
        only_after_timestamp: Only include messages created after this timestamp. If None, all messages will be included.
        rich_print: Whether to use rich to print the message
        timeout: The timeout in seconds for the streaming connection. If the connection times out, the function will return with any messages collected so far.
    Returns:
        List of TaskMessage objects collected during the session

    Raises:
        ValueError: If the task doesn't have a name (required for streaming)
    """

    messages_to_return: List[TaskMessage] = []

    # Read existing messages
    messages = []
    try:
        # List all messages for this task - MessageListResponse is just a List[TaskMessage]
        messages = client.messages.list(task_id=task.id)

    except Exception as e:
        print(f"Error reading existing messages: {e}")

    # Filter and display existing messages
    for message in messages:
        if only_after_timestamp:
            if message.created_at is not None:
                # Handle timezone comparison - make both datetimes timezone-aware
                message_time = message.created_at
                if message_time.tzinfo is None:
                    # If message time is naive, assume it's in UTC
                    message_time = message_time.replace(tzinfo=timezone.utc)

                comparison_time = only_after_timestamp
                if comparison_time.tzinfo is None:
                    # If comparison time is naive, assume it's in UTC
                    comparison_time = comparison_time.replace(tzinfo=timezone.utc)

                if message_time < comparison_time:
                    continue
                else:
                    messages_to_return.append(message)
                    print_task_message(message, print_messages, rich_print)
        else:
            messages_to_return.append(message)
            print_task_message(message, print_messages, rich_print)

    # Subscribe to server-side events using tasks.stream_by_name or stream
    # This is the proper way to get agent responses after sending an event in async agents

    # Ensure task has a name or id for streaming
    if not task.name and not task.id:
        print("Error: Task must have either name or id for streaming")
        raise ValueError("Task name or id is required")

    try:
        # Use stream_by_name (preferred) or fall back to stream (by id)
        # SDK now returns Iterator[TaskMessageUpdate] with proper SSE handling

        # Track active streaming spinners per message index
        active_spinners: dict[int, Yaspin] = {}  # index -> yaspin spinner object

        # Track pending tool calls - increment on tool_request, decrement on tool_response
        # Stream closes on 'done' only when pendingToolCalls == 0
        pending_tool_calls: int = 0

        # Choose streaming method based on available task identifier
        # SDK handles SSE parsing internally - we get typed TaskMessageUpdate events
        stream_iter = (
            client.tasks.stream_by_name(task_name=task.name)
            if task.name
            else client.tasks.stream(task_id=task.id)
        )

        try:
            for event in stream_iter:
                # Events are already typed - use isinstance for discrimination
                if isinstance(event, TaskStreamEvent_Start):
                    index = event.index or 0

                    # Start a yaspin spinner for this message
                    if print_messages and index not in active_spinners:
                        spinner = yaspin(text="🔄 Agent responding...")
                        spinner.start()
                        active_spinners[index] = spinner

                elif isinstance(event, TaskStreamEvent_Delta):
                    index = event.index or 0

                    # Track pending tool calls based on delta type
                    delta = event.delta
                    if delta is not None:
                        if isinstance(delta, TaskMessageDelta_ToolRequest):
                            # Increment pending tool calls on tool_request
                            pending_tool_calls += 1
                        elif isinstance(delta, TaskMessageDelta_ToolResponse):
                            # Decrement pending tool calls on tool_response
                            pending_tool_calls = max(0, pending_tool_calls - 1)

                    # Spinner continues running or if spinner has not been created yet, create it
                    if print_messages and index not in active_spinners:
                        spinner = yaspin(text="🔄 Agent responding...")
                        spinner.start()
                        active_spinners[index] = spinner

                elif isinstance(event, TaskStreamEvent_Full):
                    index = event.index or 0

                    # Stop spinner and show message
                    if index in active_spinners:
                        active_spinners[index].stop()
                        del active_spinners[index]
                        # Ensure clean line after spinner
                        if print_messages:
                            print()

                    if event.parent_task_message and event.parent_task_message.id:
                        finished_message = client.messages.retrieve(event.parent_task_message.id)
                        messages_to_return.append(finished_message)
                        print_task_message(finished_message, print_messages, rich_print)

                elif isinstance(event, TaskStreamEvent_Done):
                    index = event.index or 0

                    # Stop spinner and show message
                    if index in active_spinners:
                        active_spinners[index].stop()
                        del active_spinners[index]
                        # Ensure clean line after spinner
                        if print_messages:
                            print()

                    if event.parent_task_message and event.parent_task_message.id:
                        finished_message = client.messages.retrieve(event.parent_task_message.id)
                        messages_to_return.append(finished_message)
                        print_task_message(finished_message, print_messages, rich_print)

                    # Exit the streaming loop once done message is received
                    # AND there are no pending tool calls (all tool responses received)
                    if pending_tool_calls == 0:
                        break

                # Note: "connected" and "error" event types are handled by SDK internally
        finally:
            # Stop any remaining spinners when we're done
            for spinner in active_spinners.values():
                spinner.stop()
            active_spinners.clear()

    except Exception as e:
        # Handle timeout gracefully
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            if print_messages:
                print(f"Streaming timed out after {timeout} seconds - returning collected messages")
        else:
            if print_messages:
                print(f"Error subscribing to events: {e}")
                print("Make sure your agent is running and the task exists")

    return messages_to_return


# =============================================================================
# New streaming function: stream_task_events
# =============================================================================


def _handle_start(
    event: TaskStreamEvent_Start,
    state: MessageStreamState,
    can_display: bool,
) -> None:
    """Handle start event - event is already typed from SDK."""
    content = event.content

    # Use isinstance for proper discriminated union handling
    if isinstance(content, TaskMessageContent_Text):
        text = content.content
        if can_display:
            print(text, end="", flush=True)  # noqa: T201
        else:
            state.text_buffer += text
    # Other content types (ToolRequestContent, etc.) handled via deltas


def _handle_delta(
    event: TaskStreamEvent_Delta,
    state: MessageStreamState,
    console: Console,
    can_display: bool,
) -> None:
    """Handle delta event - event is already typed from SDK."""
    delta = event.delta

    if delta is None:
        return

    if isinstance(delta, TaskMessageDelta_Text):
        text = delta.text_delta or ""
        if can_display:
            print(text, end="", flush=True)  # noqa: T201
        else:
            state.text_buffer += text

    elif isinstance(delta, TaskMessageDelta_ToolRequest):
        _handle_tool_request(delta, state)

    elif isinstance(delta, TaskMessageDelta_ToolResponse):
        _handle_tool_response(delta, state)

    elif isinstance(delta, TaskMessageDelta_ReasoningContent):
        # Track by content_index - multiple reasoning blocks possible
        idx = delta.content_index
        text = delta.content_delta or ""
        if idx not in state.reasoning_buffers:
            state.reasoning_buffers[idx] = ""
        state.reasoning_buffers[idx] += text

        if can_display:
            console.print(text, style="dim italic", end="")


def _handle_tool_request(delta: TaskMessageDelta_ToolRequest, state: MessageStreamState) -> None:
    """Buffer tool request arguments - DON'T print until done event."""
    tool_id = delta.tool_call_id  # Required field

    # Create buffer if new tool_call_id
    if tool_id not in state.tool_calls:
        state.tool_calls[tool_id] = ToolCallBuffer(
            tool_call_id=tool_id,
            name=delta.name,  # Required field
        )

    buf = state.tool_calls[tool_id]
    buf.arguments_buffer += delta.arguments_delta or ""
    # Do NOT try to print here - wait for done event
    # Partial JSON like {"path": "/src"} might parse but be incomplete


def _handle_tool_response(delta: TaskMessageDelta_ToolResponse, state: MessageStreamState) -> None:
    """Buffer tool response content - print on done event."""
    tool_id = delta.tool_call_id  # Required field

    # Get or create buffer
    if tool_id not in state.tool_calls:
        state.tool_calls[tool_id] = ToolCallBuffer(
            tool_call_id=tool_id,
            name=delta.name,  # Required field
        )

    buf = state.tool_calls[tool_id]
    buf.response_buffer += delta.content_delta or ""


def _print_tool_request(
    buf: ToolCallBuffer,
    console: Console,
    verbose: bool = False,
) -> None:
    """Print a tool request in a clean, ASCII-friendly format."""
    if buf.request_printed or not buf.arguments_buffer:
        return

    print()  # noqa: T201
    console.print(f"[{buf.name}]", style="yellow bold")
    try:
        args = json.loads(buf.arguments_buffer)
        for key, value in args.items():
            if isinstance(value, str):
                if "\n" in value or len(value) > 70:
                    # Multi-line or long value
                    if verbose:
                        # Show full content with proper indentation (use print to avoid Rich wrapping)
                        print(f"  | {key}:")  # noqa: T201
                        for line in value.split("\n"):
                            print(f"  |   {line}")  # noqa: T201
                    else:
                        # Truncate for compact display
                        display_val = value.replace("\n", " ")
                        if len(display_val) > 70:
                            display_val = display_val[:67] + "..."
                        print(f"  | {key}: {display_val}")  # noqa: T201
                else:
                    print(f"  | {key}: {value}")  # noqa: T201
            else:
                display_val = json.dumps(value)
                if len(display_val) > 70 and not verbose:
                    display_val = display_val[:67] + "..."
                print(f"  | {key}: {display_val}")  # noqa: T201
    except json.JSONDecodeError:
        print(f"  | {buf.arguments_buffer[:80]}")  # noqa: T201
    buf.request_printed = True


def _print_tool_response(
    buf: ToolCallBuffer,
    console: Console,
    verbose: bool = False,
    max_lines: int = 15,
) -> None:
    """Print a tool response with full content."""
    if buf.response_printed or not buf.response_buffer:
        return

    # Clean up the response - remove line numbers and system reminders
    response = buf.response_buffer

    # Remove system reminder blocks entirely (they can span multiple lines)
    response = re.sub(r"<system-reminder>.*?</system-reminder>", "", response, flags=re.DOTALL)

    # Strip common noise patterns line by line
    lines = response.split("\n")
    clean_lines = []
    in_system_reminder = False
    for line in lines:
        # Track multi-line system reminders
        if "<system-reminder>" in line:
            in_system_reminder = True
            continue
        if "</system-reminder>" in line:
            in_system_reminder = False
            continue
        if in_system_reminder:
            continue
        # Skip lines that are just "Whenever you read a file..." noise
        if "Whenever you read a file" in line:
            continue
        # Strip line number prefixes like "     1→" or "    12→"
        line = re.sub(r"^\s*\d+→", "", line)
        # Keep the line (even if empty, for formatting)
        clean_lines.append(line.rstrip())

    # Remove leading/trailing empty lines
    while clean_lines and not clean_lines[0].strip():
        clean_lines.pop(0)
    while clean_lines and not clean_lines[-1].strip():
        clean_lines.pop()

    if not clean_lines:
        console.print("  '--> (empty)", style="green dim")
        buf.response_printed = True
        return

    # Print response with proper indentation (use print to avoid Rich wrapping)
    if len(clean_lines) == 1:
        # Single line - inline
        console.print(f"  '--> {clean_lines[0]}", style="green")
    else:
        # Multi-line - show each line indented
        console.print("  '-->", style="green")
        lines_to_show = clean_lines if verbose else clean_lines[:max_lines]
        for line in lines_to_show:
            print(f"       {line}")  # noqa: T201
        if not verbose and len(clean_lines) > max_lines:
            console.print(f"       ... ({len(clean_lines) - max_lines} more lines)", style="dim italic")

    buf.response_printed = True
    print()  # noqa: T201  # Blank line after tool output


def _flush_pending_tools(
    state: MessageStreamState,
    console: Console,
    can_display: bool,
    verbose: bool = False,
) -> None:
    """Print any remaining tool requests/responses that have responses."""
    if not can_display:
        return

    # Only print tools that have responses - keeps request+response paired
    for buf in state.tool_calls.values():
        if buf.response_buffer:
            _print_tool_request(buf, console, verbose=verbose)
            _print_tool_response(buf, console, verbose=verbose)


def _flush_buffered_messages(
    messages: dict[int, MessageStreamState],
    current_index: int,
    console: Console,
    verbose: bool = False,
) -> None:
    """Replay buffered content for messages that can now be displayed."""
    if current_index not in messages:
        return

    state = messages[current_index]

    # Print buffered text
    if state.text_buffer:
        print(state.text_buffer, end="", flush=True)  # noqa: T201
        state.text_buffer = ""

    # Print buffered reasoning (all content_index blocks)
    for idx in sorted(state.reasoning_buffers.keys()):
        text = state.reasoning_buffers[idx]
        if text:
            console.print(text, style="dim italic", end="")
    state.reasoning_buffers.clear()

    # Print buffered tool calls
    _flush_pending_tools(state, console, can_display=True, verbose=verbose)

    # If this message was already done, advance to next
    if state.is_done:
        print()  # noqa: T201  # Newline
        _flush_buffered_messages(messages, current_index + 1, console, verbose=verbose)


class IdleTimeoutError(Exception):
    """Raised when idle timeout expires after receiving content."""
    pass


def stream_task_events(
    client: TerminalUse,
    task: Task | TaskResponse,
    timeout: int = 600,
    debug: bool = False,
    verbose: bool = False,
    idle_timeout: float = 4.0,
) -> None:
    """
    Stream task events with true character-level streaming for CLI display.

    This function provides real-time streaming output:
    - Text: Printed character-by-character as deltas arrive
    - Tool requests: Buffered until JSON is complete, then displayed
    - Tool responses: Buffered until complete, then displayed
    - Reasoning: Printed dim/italic as deltas arrive

    Sequential message handling ensures index=0 completes before index=1.

    Args:
        client: The TerminalUse client instance
        task: The task to stream events for
        timeout: Connection timeout in seconds (default 600 = 10 minutes)
        debug: If True, print raw SSE events for debugging
        verbose: If True, show full tool arguments and responses without truncation
        idle_timeout: Seconds to wait after receiving a full message before closing
                     if no more events arrive (default 4.0). Set to 0 to disable.

    Returns:
        None (display-only function)

    Raises:
        ValueError: If task has neither name nor id
    """
    import signal

    console = Console()
    messages: dict[int, MessageStreamState] = {}
    current_index = 0
    # Track pending tool calls - don't close until all tools have responses
    pending_tool_call_ids: set[str] = set()
    # Track if we've received any streaming content (start/delta events).
    # If so, we'll get a done event for sure and shouldn't use idle timeout.
    has_streamed = False

    def idle_timeout_handler(signum: int, frame: object) -> None:
        """Signal handler for idle timeout - raises exception to exit stream loop."""
        raise IdleTimeoutError("Idle timeout after receiving content")

    def start_idle_timer() -> None:
        """Start the idle timer using SIGALRM (Unix only)."""
        if idle_timeout <= 0:
            return
        try:
            signal.signal(signal.SIGALRM, idle_timeout_handler)
            signal.alarm(int(idle_timeout))
            if debug:
                print(f"DEBUG: Started idle timer ({idle_timeout}s)", flush=True)  # noqa: T201
        except (AttributeError, ValueError):
            # SIGALRM not available (Windows) or invalid - skip idle timeout
            pass

    def cancel_idle_timer() -> None:
        """Cancel the idle timer."""
        try:
            signal.alarm(0)
        except (AttributeError, ValueError):
            pass

    # Ensure task has a name or id for streaming
    if not task.name and not task.id:
        raise ValueError("Task name or id is required")

    # Choose streaming method based on available task identifier
    # SDK handles SSE parsing internally - we get typed TaskMessageUpdate events
    if debug:
        if task.name:
            print(f"DEBUG: Streaming by name: {task.name}", flush=True)  # noqa: T201
        else:
            print(f"DEBUG: Streaming by id: {task.id}", flush=True)  # noqa: T201

    stream_iter = (
        client.tasks.stream_by_name(task_name=task.name)
        if task.name
        else client.tasks.stream(task_id=task.id)
    )

    try:
        if debug:
            print("DEBUG: Connected to stream", flush=True)  # noqa: T201

        for event in stream_iter:
            # Handle null index - treat as 0
            index = getattr(event, "index", None) or 0
            if debug:
                print(f"DEBUG: type={type(event).__name__} index={index}", flush=True)  # noqa: T201

            # Ensure state exists
            if index not in messages:
                messages[index] = MessageStreamState(index=index)
            state = messages[index]

            # Can only display if it's our turn (sequential)
            can_display = index == current_index

            if isinstance(event, TaskStreamEvent_Start):
                # Cancel idle timer - more content coming
                cancel_idle_timer()
                has_streamed = True
                _handle_start(event, state, can_display)

            elif isinstance(event, TaskStreamEvent_Delta):
                # Cancel idle timer - more content coming
                cancel_idle_timer()
                has_streamed = True
                # Track pending tool calls before delegating to handler
                delta = event.delta
                if delta is not None:
                    if isinstance(delta, TaskMessageDelta_ToolRequest):
                        # Add to pending - we need to wait for response
                        pending_tool_call_ids.add(delta.tool_call_id)
                        if debug:
                            print(f"DEBUG: Added pending tool: {delta.tool_call_id}", flush=True)  # noqa: T201
                    elif isinstance(delta, TaskMessageDelta_ToolResponse):
                        # Remove from pending - response received
                        pending_tool_call_ids.discard(delta.tool_call_id)
                        if debug:
                            print(f"DEBUG: Removed pending tool: {delta.tool_call_id}, remaining: {pending_tool_call_ids}", flush=True)  # noqa: T201
                _handle_delta(event, state, console, can_display)

            elif isinstance(event, TaskStreamEvent_Full):
                # Handle full message events (non-streaming messages)
                content = event.content

                if isinstance(content, TaskMessageContent_Text):
                    # Print text content directly
                    text = content.content or ""
                    if can_display and text:
                        print(text, flush=True)  # noqa: T201
                    elif text:
                        state.text_buffer += text
                    if debug:
                        print("DEBUG: Printed full text message", flush=True)  # noqa: T201

                elif isinstance(content, TaskMessageContent_ToolResponse):
                    tool_call_id = content.tool_call_id
                    if tool_call_id:
                        pending_tool_call_ids.discard(tool_call_id)
                        # Capture response content and print immediately
                        if tool_call_id in state.tool_calls:
                            buf = state.tool_calls[tool_call_id]
                            response_content = content.content or ""
                            if isinstance(response_content, str):
                                buf.response_buffer = response_content
                            else:
                                buf.response_buffer = json.dumps(response_content)
                            # Print request first if not yet printed, then response
                            if can_display:
                                _print_tool_request(buf, console, verbose=verbose)
                                _print_tool_response(buf, console, verbose=verbose)
                        if debug:
                            print(f"DEBUG: Printed tool response: {tool_call_id}", flush=True)  # noqa: T201

                # Only start idle timer if we haven't received streaming content.
                # If streaming has occurred, we'll get a done event for sure.
                if not has_streamed:
                    start_idle_timer()

            elif isinstance(event, TaskStreamEvent_Done):
                # Cancel idle timer - explicit done received
                cancel_idle_timer()
                state.is_done = True
                # Flush any pending tool responses for this message
                _flush_pending_tools(state, console, can_display, verbose=verbose)

                # Only close if no pending tool calls - otherwise wait for responses
                if len(pending_tool_call_ids) == 0:
                    if index == current_index:
                        print()  # noqa: T201  # Newline after message
                        current_index += 1
                        # Flush buffered content for next message(s)
                        _flush_buffered_messages(messages, current_index, console, verbose=verbose)

                    if debug:
                        print("DEBUG: No pending tools, closing stream", flush=True)  # noqa: T201
                    break
                else:
                    if debug:
                        print(f"DEBUG: Waiting for {len(pending_tool_call_ids)} pending tool(s): {pending_tool_call_ids}", flush=True)  # noqa: T201

    except IdleTimeoutError:
        # Normal exit after idle timeout - content was received, no more events
        if debug:
            print("DEBUG: Idle timeout - closing stream gracefully", flush=True)  # noqa: T201
        print()  # noqa: T201  # Newline after content
    except Exception as e:
        # Keep partial content displayed, show error
        if "timeout" in str(e).lower():
            # Only treat as timeout if we haven't received streaming content.
            # If streaming has started, we're expecting a done event.
            if not has_streamed:
                console.print("\n[yellow]Connection timed out[/yellow]")
            elif debug:
                print(f"DEBUG: Timeout occurred but streaming started, ignoring: {e}", flush=True)  # noqa: T201
        else:
            console.print(f"\n[red]Disconnected: {e}[/red]")
    finally:
        # Clean up idle timer
        cancel_idle_timer()
