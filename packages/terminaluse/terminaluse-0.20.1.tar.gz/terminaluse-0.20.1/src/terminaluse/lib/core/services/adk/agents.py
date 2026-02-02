from typing import Optional

from terminaluse import AsyncTerminalUse
from terminaluse.types.agent import Agent
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.temporal import heartbeat_if_in_workflow
from terminaluse.lib.core.tracing.tracer import AsyncTracer

logger = make_logger(__name__)


class AgentsService:
    def __init__(
        self,
        terminaluse_client: AsyncTerminalUse,
        tracer: AsyncTracer,
    ):
        self._terminaluse_client = terminaluse_client
        self._tracer = tracer

    async def get_agent(
        self,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Agent:
        trace = self._tracer.trace(trace_id)
        async with trace.span(
            parent_id=parent_span_id,
            name="get_agent",
            input={"agent_id": agent_id, "agent_name": agent_name},
        ) as span:
            heartbeat_if_in_workflow("get agent")
            if agent_id:
                agent = await self._terminaluse_client.agents.retrieve(agent_id=agent_id)
            elif agent_name:
                agent = await self._terminaluse_client.agents.retrieve_by_name(agent_name=agent_name)
            else:
                raise ValueError("Either agent_id or agent_name must be provided")
            if span:
                span.output = agent.model_dump()
            return agent
