from abc import ABC, abstractmethod

from temporalio import workflow

from terminaluse.lib.types.acp import SendEventParams, CreateTaskParams
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.core.temporal.types.workflow import SignalName

logger = make_logger(__name__)


class BaseWorkflow(ABC):
    def __init__(
        self,
        display_name: str,
    ):
        self.display_name = display_name

    @abstractmethod
    @workflow.signal(name=SignalName.RECEIVE_EVENT)
    async def on_event(self, params: SendEventParams) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_create(self, params: CreateTaskParams) -> None:
        raise NotImplementedError
