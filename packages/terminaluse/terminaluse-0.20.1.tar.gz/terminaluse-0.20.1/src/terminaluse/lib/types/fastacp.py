from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, BaseModel, field_validator


class BaseACPConfig(BaseModel):
    """
    Base configuration for all ACP implementations

    Attributes:
        type: The type of ACP implementation
    """

    pass


class AsyncACPConfig(BaseACPConfig):
    """
    Base class for async ACP configurations

    Attributes:
        type: The type of ACP implementation
    """

    type: Literal["temporal", "base"] = Field(..., frozen=True)


class TemporalACPConfig(AsyncACPConfig):
    """
    Configuration for TemporalACP implementation

    Attributes:
        type: The type of ACP implementation
        temporal_address: The address of the temporal server
        plugins: List of Temporal client plugins
        interceptors: List of Temporal worker interceptors
    """

    type: Literal["temporal"] = Field(default="temporal", frozen=True)
    temporal_address: str = Field(default="temporal-frontend.temporal.svc.cluster.local:7233", frozen=True)
    plugins: list[Any] = Field(default=[], frozen=True)
    interceptors: list[Any] = Field(default=[], frozen=True)

    @field_validator("plugins")
    @classmethod
    def validate_plugins(cls, v: list[Any]) -> list[Any]:
        """Validate that all plugins are valid Temporal client plugins."""
        from terminaluse.lib.core.clients.temporal.utils import validate_client_plugins

        validate_client_plugins(v)
        return v

    @field_validator("interceptors")
    @classmethod
    def validate_interceptors(cls, v: list[Any]) -> list[Any]:
        """Validate that all interceptors are valid Temporal worker interceptors."""
        from terminaluse.lib.core.clients.temporal.utils import validate_worker_interceptors

        validate_worker_interceptors(v)
        return v


class AsyncBaseACPConfig(AsyncACPConfig):
    """Configuration for AsyncBaseACP implementation

    Attributes:
        type: The type of ACP implementation
    """

    type: Literal["base"] = Field(default="base", frozen=True)
