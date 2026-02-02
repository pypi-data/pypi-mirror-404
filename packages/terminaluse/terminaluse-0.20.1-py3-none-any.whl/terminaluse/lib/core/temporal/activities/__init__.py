import httpx

from terminaluse import AsyncTerminalUse  # noqa: F401
from terminaluse.lib.core.tracing import AsyncTracer
from terminaluse.lib.core.services.adk.state import StateService
from terminaluse.lib.core.services.adk.tasks import TasksService
from terminaluse.lib.core.services.adk.events import EventsService
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client
from terminaluse.lib.core.services.adk.acp.acp import ACPService
from terminaluse.lib.core.services.adk.tracing import TracingService
from terminaluse.lib.core.services.adk.messages import MessagesService
from terminaluse.lib.core.services.adk.streaming import StreamingService
from terminaluse.lib.core.services.adk.utils.templating import TemplatingService
from terminaluse.lib.core.services.adk.agent_task_tracker import AgentTaskTrackerService
from terminaluse.lib.core.temporal.activities.adk.state_activities import StateActivities
from terminaluse.lib.core.temporal.activities.adk.tasks_activities import TasksActivities
from terminaluse.lib.core.temporal.activities.adk.events_activities import EventsActivities
from terminaluse.lib.core.temporal.activities.adk.acp.acp_activities import ACPActivities
from terminaluse.lib.core.temporal.activities.adk.tracing_activities import TracingActivities
from terminaluse.lib.core.temporal.activities.adk.messages_activities import MessagesActivities
from terminaluse.lib.core.temporal.activities.adk.streaming_activities import (
    StreamingActivities,
)
from terminaluse.lib.core.temporal.activities.adk.utils.templating_activities import (
    TemplatingActivities,
)
from terminaluse.lib.core.temporal.activities.adk.agent_task_tracker_activities import (
    AgentTaskTrackerActivities,
)


def get_all_activities():
    """
    Returns a list of all standard activity functions that can be directly passed to worker.run().

    Returns:
        list: A list of activity functions ready to be passed to worker.run()
    """
    # Initialize common dependencies
    terminaluse_client = create_async_terminaluse_client(
        timeout=httpx.Timeout(timeout=1000),
    )
    tracer = AsyncTracer(terminaluse_client)

    # Services

    ## ADK
    streaming_service = StreamingService(
        terminaluse_client=terminaluse_client,
    )
    messages_service = MessagesService(
        terminaluse_client=terminaluse_client,
        streaming_service=streaming_service,
        tracer=tracer,
    )
    events_service = EventsService(
        terminaluse_client=terminaluse_client,
        tracer=tracer,
    )
    agent_task_tracker_service = AgentTaskTrackerService(
        terminaluse_client=terminaluse_client,
        tracer=tracer,
    )
    state_service = StateService(
        terminaluse_client=terminaluse_client,
        tracer=tracer,
    )
    tasks_service = TasksService(
        terminaluse_client=terminaluse_client,
        tracer=tracer,
    )
    tracing_service = TracingService(
        tracer=tracer,
    )

    ## ACP
    acp_service = ACPService(
        terminaluse_client=terminaluse_client,
        tracer=tracer,
    )

    ## Utils
    templating_service = TemplatingService(
        tracer=tracer,
    )

    # ADK

    ## Core activities
    messages_activities = MessagesActivities(messages_service=messages_service)
    events_activities = EventsActivities(events_service=events_service)
    agent_task_tracker_activities = AgentTaskTrackerActivities(agent_task_tracker_service=agent_task_tracker_service)
    state_activities = StateActivities(state_service=state_service)
    streaming_activities = StreamingActivities(streaming_service=streaming_service)
    tasks_activities = TasksActivities(tasks_service=tasks_service)
    tracing_activities = TracingActivities(tracing_service=tracing_service)

    ## ACP
    acp_activities = ACPActivities(acp_service=acp_service)

    ## Utils
    templating_activities = TemplatingActivities(templating_service=templating_service)

    # Build list of standard activities
    activities = [
        # Core activities
        ## Messages activities
        messages_activities.send,
        messages_activities.update_message,
        messages_activities.send_batch,
        messages_activities.update_messages_batch,
        messages_activities.list_messages,
        ## Events activities
        events_activities.get_event,
        events_activities.list,
        ## Agent Task Tracker activities
        agent_task_tracker_activities.get_agent_task_tracker,
        agent_task_tracker_activities.get_agent_task_tracker_by_task_and_agent,
        agent_task_tracker_activities.update_agent_task_tracker,
        ## State activities
        state_activities.create_state,
        state_activities.get,
        state_activities.update,
        state_activities.delete_state,
        ## Streaming activities
        streaming_activities.stream_update,
        ## Tasks activities
        tasks_activities.get_task,
        tasks_activities.delete_task,
        ## Tracing activities
        tracing_activities.start_span,
        tracing_activities.end_span,
        # ACP activities
        acp_activities.task_create,
        acp_activities.event_send,
        acp_activities.task_cancel,
        # Utils
        templating_activities.render_jinja,
    ]

    return activities
