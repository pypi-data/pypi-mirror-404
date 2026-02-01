"""TaskContext - Context object for agent handlers with pre-bound task/agent IDs.

This module provides a streamlined API for agent handlers by injecting a context
object with pre-bound task and agent identifiers. Module wrappers automatically
inject task_id and agent_id to reduce boilerplate.

Example usage:
    from terminaluse import AgentServer, TaskContext, Event
    from terminaluse.types.text_content import TextContent

    server = AgentServer()

    @server.on_create
    async def handle_create(ctx: TaskContext, params: dict[str, Any]):
        print(f"Task: {ctx.task.id}")
        await ctx.state.create(state={"initialized": True})
        await ctx.messages.send(TextContent(author="agent", content="Task created!"))

    @server.on_event
    async def handle_event(ctx: TaskContext, event: Event):
        await ctx.messages.send(TextContent(author="agent", content=f"Received: {event.content}"))

    @server.on_cancel
    async def handle_cancel(ctx: TaskContext):
        await ctx.messages.send(TextContent(author="agent", content="Cancelled"))
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from terminaluse.types.task import Task
from terminaluse.types.agent import Agent
from terminaluse.types.event import Event
from terminaluse.types.state import State
from terminaluse.lib.utils.temporal import in_temporal_workflow
from terminaluse.types.task_message import TaskMessage
from terminaluse.types.task_message_content import TaskMessageContent

if TYPE_CHECKING:
    from terminaluse.lib.core.services.adk.streaming import StreamingTaskMessageContext


class ContextMessagesModule:
    """Messages module with task_id auto-injected.

    Provides all message operations from adk.messages with task_id automatically
    bound from the TaskContext.
    """

    def __init__(self, task_id: str):
        self._task_id = task_id

    async def send(self, content: TaskMessageContent | str, **kwargs: Any) -> TaskMessage:
        """Send a message for this task.

        Args:
            content: The message content to send. Can be a TaskMessageContent object
                or a string (which will be wrapped in TextContent with author="agent").
            **kwargs: Additional arguments passed to adk.messages.send.

        Returns:
            The created TaskMessage.
        """
        from terminaluse.lib import adk
        from terminaluse.types import TaskMessageContent_Text

        # Auto-wrap string in TaskMessageContent_Text (has the discriminator field)
        if isinstance(content, str):
            content = TaskMessageContent_Text(author="agent", content=content)

        return await adk.messages.send(task_id=self._task_id, content=content, **kwargs)

    async def list(self, **kwargs: Any) -> builtins.list[TaskMessage]:
        """List messages for this task.

        Args:
            **kwargs: Additional arguments passed to adk.messages.list.

        Returns:
            List of TaskMessages for this task.
        """
        from terminaluse.lib import adk

        return await adk.messages.list(task_id=self._task_id, **kwargs)

    async def update(
        self, message_id: str, content: TaskMessageContent, **kwargs: Any
    ) -> TaskMessage:
        """Update a message for this task.

        Args:
            message_id: The ID of the message to update.
            content: The new message content.
            **kwargs: Additional arguments passed to adk.messages.update.

        Returns:
            The updated TaskMessage.
        """
        from terminaluse.lib import adk

        return await adk.messages.update(
            task_id=self._task_id, message_id=message_id, content=content, **kwargs
        )

    async def send_batch(
        self, contents: builtins.list[TaskMessageContent], **kwargs: Any
    ) -> builtins.list[TaskMessage]:
        """Send a batch of messages for this task.

        Args:
            contents: List of message contents to send.
            **kwargs: Additional arguments passed to adk.messages.send_batch.

        Returns:
            List of created TaskMessages.
        """
        from terminaluse.lib import adk

        return await adk.messages.send_batch(
            task_id=self._task_id, contents=contents, **kwargs
        )

    async def update_batch(
        self, updates: dict[str, TaskMessageContent], **kwargs: Any
    ) -> builtins.list[TaskMessage]:
        """Update a batch of messages for this task.

        Args:
            updates: Dict mapping message_id to new content.
            **kwargs: Additional arguments passed to adk.messages.update_batch.

        Returns:
            List of updated TaskMessages.
        """
        from terminaluse.lib import adk

        return await adk.messages.update_batch(
            task_id=self._task_id, updates=updates, **kwargs
        )


class ContextStateModule:
    """State module with task_id and agent_id auto-injected.

    Provides all state operations from adk.state with task_id and agent_id
    automatically bound from the TaskContext.
    """

    def __init__(self, task_id: str, agent_id: str):
        self._task_id = task_id
        self._agent_id = agent_id

    async def create(self, state: dict[str, Any], **kwargs: Any) -> State:
        """Create state for this task/agent.

        Args:
            state: The state dictionary to create.
            **kwargs: Additional arguments passed to adk.state.create.

        Returns:
            The created State object.
        """
        from terminaluse.lib import adk

        return await adk.state.create(
            task_id=self._task_id, agent_id=self._agent_id, state=state, **kwargs
        )

    async def get(self, **kwargs: Any) -> dict[str, Any] | None:
        """Get state for this task/agent.

        Args:
            **kwargs: Additional arguments passed to adk.state.get.

        Returns:
            The state dictionary if found, None otherwise.
        """
        from terminaluse.lib import adk

        state_obj = await adk.state.get(
            task_id=self._task_id, agent_id=self._agent_id, **kwargs
        )
        return state_obj.state if state_obj else None

    async def update(self, state: dict[str, Any], **kwargs: Any) -> State:
        """Update state for this task/agent.

        Args:
            state: The new state dictionary.
            **kwargs: Additional arguments passed to adk.state.update.

        Returns:
            The updated State object.
        """
        from terminaluse.lib import adk

        return await adk.state.update(
            state, task_id=self._task_id, agent_id=self._agent_id, **kwargs
        )

    async def delete(self, state_id: str, **kwargs: Any) -> State:
        """Delete a state by ID.

        Args:
            state_id: The ID of the state to delete.
            **kwargs: Additional arguments passed to adk.state.delete.

        Returns:
            The deleted State object.
        """
        from terminaluse.lib import adk

        return await adk.state.delete(state_id=state_id, **kwargs)


class ContextEventsModule:
    """Events module with task_id and agent_id auto-injected.

    Provides event operations from adk.events with task_id and agent_id
    automatically bound from the TaskContext.
    """

    def __init__(self, task_id: str, agent_id: str):
        self._task_id = task_id
        self._agent_id = agent_id

    async def list(self, **kwargs: Any) -> builtins.list[Event]:
        """List events for this task/agent.

        Args:
            **kwargs: Additional arguments passed to adk.events.list.

        Returns:
            List of Event objects.
        """
        from terminaluse.lib import adk

        return await adk.events.list(
            task_id=self._task_id, agent_id=self._agent_id, **kwargs
        )

    async def get(self, event_id: str, **kwargs: Any) -> Event | None:
        """Get an event by ID.

        Args:
            event_id: The ID of the event to retrieve.
            **kwargs: Additional arguments passed to adk.events.get.

        Returns:
            The Event object if found, None otherwise.
        """
        from terminaluse.lib import adk

        return await adk.events.get(event_id=event_id, **kwargs)

    async def send(
        self,
        content: TaskMessageContent,
        agent_id: str | None = None,
        agent_name: str | None = None,
        **kwargs: Any,
    ) -> Event:
        """Send an event to this task.

        This triggers the on_event handler of the agent handling this task.
        By default, sends to the current agent, but can target a different agent
        by providing agent_id or agent_name.

        Args:
            content: The content of the event to send.
            agent_id: Optional agent ID to target (defaults to current agent).
            agent_name: Optional agent name to target.
            **kwargs: Additional arguments passed to adk.events.send.

        Returns:
            The created Event object.
        """
        from terminaluse.lib import adk

        return await adk.events.send(
            task_id=self._task_id,
            content=content,
            agent_id=agent_id if agent_id is not None else self._agent_id,
            agent_name=agent_name,
            **kwargs,
        )


class ContextStreamingModule:
    """Streaming module with task_id auto-injected.

    Provides streaming operations from adk.streaming with task_id automatically
    bound from the TaskContext.

    Note: Streaming is not supported in Temporal workflows. Use ctx.messages.send()
    instead when running in a Temporal context.
    """

    def __init__(self, task_id: str):
        self._task_id = task_id

    def streaming_task_message_context(
        self, initial_content: TaskMessageContent
    ) -> "StreamingTaskMessageContext":
        """Create a streaming context for this task.

        Args:
            initial_content: The initial content for the streaming message.

        Returns:
            A StreamingTaskMessageContext for managing the streaming lifecycle.

        Raises:
            RuntimeError: If called from within a Temporal workflow.
        """
        if in_temporal_workflow():
            raise RuntimeError(
                "Streaming is not supported in Temporal workflows. "
                "Use ctx.messages.send() instead for sending messages in Temporal contexts."
            )
        from terminaluse.lib import adk

        return adk.streaming.streaming_task_message_context(
            task_id=self._task_id, initial_content=initial_content
        )


class TaskContext:
    """Context object passed to handler functions with pre-bound task/agent IDs.

    TaskContext provides a streamlined API for agent handlers by:
    - Exposing the full Task and Agent models for accessing metadata
    - Providing module wrappers that auto-inject task_id and agent_id

    Attributes:
        task: The full Task model (access task.id, task.created_at, etc.)
        agent: The full Agent model (access agent.id, agent.name, etc.)
        request: Optional request metadata (headers, etc.)
        messages: Messages module with task_id auto-injected
        state: State module with task_id and agent_id auto-injected
        events: Events module with task_id and agent_id auto-injected
        streaming: Streaming module with task_id auto-injected

    Example:
        @server.on_event
        async def handle_event(ctx: TaskContext, event: Event):
            # Access task/agent metadata
            print(f"Task {ctx.task.id} created at {ctx.task.created_at}")

            # Use auto-injected modules
            await ctx.state.create(state={"key": "value"})
            messages = await ctx.messages.list()

            # Send a message
            await ctx.messages.send(TextContent(author="agent", content="Hello!"))
    """

    def __init__(
        self,
        task: Task,
        agent: Agent,
        request: dict[str, Any] | None,
    ):
        """Initialize TaskContext with task, agent, and request data.

        Args:
            task: The Task model for the current task.
            agent: The Agent model for the current agent.
            request: Optional request metadata dict (e.g., headers).
        """
        self.task = task
        self.agent = agent
        self.request = request

        # Module wrappers (cheap - only hold IDs, not clients)
        self.messages = ContextMessagesModule(task.id)
        self.state = ContextStateModule(task.id, agent.id)
        self.events = ContextEventsModule(task.id, agent.id)
        self.streaming = ContextStreamingModule(task.id)
