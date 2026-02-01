from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.model_utils import BaseModel
from terminaluse.lib.types.agent_configs import TemporalConfig, TemporalWorkflowConfig

logger = make_logger(__name__)


# SDK type options for agent runtime
SdkType = Literal["claude_agent_sdk"]


class AgentConfig(BaseModel):
    name: str = Field(
        ...,
        description="Agent identifier in namespace_slug/agent_name format (e.g., 'acme-corp/my-agent')",
        pattern=r"^[a-z0-9-]+/[a-z0-9-]+$",
    )

    @property
    def namespace_slug(self) -> str:
        """Extract namespace slug from full name (e.g., 'acme-corp' from 'acme-corp/my-agent')"""
        return self.name.split("/")[0]

    @property
    def short_name(self) -> str:
        """Extract agent name from full name (e.g., 'my-agent' from 'acme-corp/my-agent')"""
        return self.name.split("/")[1]

    entrypoint: str = Field(
        default="src.agent:server",
        description="ASGI app entrypoint in uvicorn format: 'module.path:app_variable' (e.g., 'src.agent:server'). "
        "Used to start the agent and derive the code directory for sandboxing.",
    )

    @property
    def code_subdir(self) -> str:
        """Extract code subdirectory from entrypoint (e.g., 'src' from 'src.agent:server')."""
        module_path = self.entrypoint.split(":")[0]  # 'src.agent'
        return module_path.split(".")[0]  # 'src'

    description: str = Field(..., description="The description of the agent.")
    temporal: TemporalConfig | None = Field(default=None, description="Temporal workflow configuration for this agent")
    sdk_type: Optional[SdkType] = Field(
        default=None,
        description="SDK type for agent runtime. Defaults to 'claude_agent_sdk' if not specified.",
    )

    def is_temporal_agent(self) -> bool:
        """Check if this agent uses Temporal workflows"""
        # Check temporal config with enabled flag
        if self.temporal and self.temporal.enabled:
            return True
        return False

    def get_temporal_workflow_config(self) -> TemporalWorkflowConfig | None:
        """Get temporal workflow configuration, checking both new and legacy formats"""
        # Check new workflows list first
        if self.temporal and self.temporal.enabled and self.temporal.workflows:
            return self.temporal.workflows[0]  # Return first workflow for backward compatibility

        # Check legacy single workflow
        if self.temporal and self.temporal.enabled and self.temporal.workflow:
            return self.temporal.workflow

        return None

    def get_temporal_workflows(self) -> list[TemporalWorkflowConfig]:
        """Get all temporal workflow configurations"""
        # Check new workflows list first
        if self.temporal and self.temporal.enabled and self.temporal.workflows:
            return self.temporal.workflows

        # Check legacy single workflow
        if self.temporal and self.temporal.enabled and self.temporal.workflow:
            return [self.temporal.workflow]

        return []
