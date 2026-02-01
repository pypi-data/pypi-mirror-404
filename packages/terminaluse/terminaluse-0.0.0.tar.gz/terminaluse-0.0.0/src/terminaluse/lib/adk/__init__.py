# ruff: noqa: I001
# Import order matters here to avoid circular imports
# The _modules must be imported before utils

from terminaluse.lib.adk._modules.acp import ACPModule
from terminaluse.lib.adk._modules.agents import AgentsModule
from terminaluse.lib.adk._modules.agent_task_tracker import AgentTaskTrackerModule
from terminaluse.lib.adk._modules.events import EventsModule
from terminaluse.lib.adk._modules.messages import MessagesModule
from terminaluse.lib.adk._modules.state import StateModule
from terminaluse.lib.adk._modules.streaming import StreamingModule
from terminaluse.lib.adk._modules.tasks import TasksModule
from terminaluse.lib.adk._modules.tracing import TracingModule
from terminaluse.lib.adk._modules.filesystem import FilesystemModule
from terminaluse.lib.adk._modules.task import TaskModule

from terminaluse.lib.adk import utils

acp = ACPModule()
agents = AgentsModule()
tasks = TasksModule()
messages = MessagesModule()
state = StateModule()
streaming = StreamingModule()
tracing = TracingModule()
events = EventsModule()
agent_task_tracker = AgentTaskTrackerModule()
filesystem = FilesystemModule()
task = TaskModule()

__all__ = [
    # Core
    "acp",
    "agents",
    "tasks",
    "messages",
    "state",
    "streaming",
    "tracing",
    "events",
    "agent_task_tracker",
    "filesystem",
    "task",
    # Utils
    "utils",
]
