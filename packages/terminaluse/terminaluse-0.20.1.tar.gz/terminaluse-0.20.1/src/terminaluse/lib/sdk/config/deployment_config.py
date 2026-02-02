from __future__ import annotations

from pydantic import Field

from terminaluse.lib.utils.model_utils import BaseModel


class ResourceRequirements(BaseModel):
    """Resource requirements for containers"""

    cpu: str = Field(default="500m", description="CPU request/limit (e.g., '500m', '1')")
    memory: str = Field(default="1Gi", description="Memory request/limit (e.g., '1Gi', '512Mi')")


class ResourceConfig(BaseModel):
    """Resource configuration for containers"""

    requests: ResourceRequirements = Field(default_factory=ResourceRequirements, description="Resource requests")
    limits: ResourceRequirements = Field(default_factory=ResourceRequirements, description="Resource limits")


class EnvironmentDeploymentConfig(BaseModel):
    """Configuration for a specific environment (production or preview)"""

    replicaCount: int = Field(default=1, ge=1, le=10, description="Number of replicas to deploy (1-10)")
    resources: ResourceConfig = Field(default_factory=ResourceConfig, description="Resource requirements")
    areTasksSticky: bool | None = Field(
        default=None,
        description="If true, running tasks stay on their original version until completion during deploys. "
        "Defaults to true for production, false for preview.",
    )


class DeploymentConfig(BaseModel):
    """Main deployment configuration in the manifest.

    Contains environment-specific configurations for production and preview.
    The CLI resolves which environment to use based on the branch being deployed.
    """

    production: EnvironmentDeploymentConfig = Field(
        default_factory=EnvironmentDeploymentConfig,
        description="Configuration for production environment (main branch)",
    )
    preview: EnvironmentDeploymentConfig = Field(
        default_factory=EnvironmentDeploymentConfig,
        description="Configuration for preview environments (feature branches)",
    )
