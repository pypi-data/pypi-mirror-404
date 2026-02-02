from __future__ import annotations

import os
import inspect
from typing import Literal
from pathlib import Path

from terminaluse.lib.types.fastacp import (
    BaseACPConfig,
    AsyncACPConfig,
)
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sdk.fastacp.impl.temporal_acp import TemporalACP
from terminaluse.lib.sdk.fastacp.impl.async_base_acp import AsyncBaseACP
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer

# Mapping between async ACP sub-types and implementations
ASYNC_ACP_IMPLEMENTATIONS: dict[Literal["temporal", "base"], type[BaseACPServer]] = {
    "temporal": TemporalACP,
    "base": AsyncBaseACP,
}

logger = make_logger(__name__)


class FastACP:
    """Factory for creating FastACP instances

    Supports async ACP with sub-types "base" or "temporal" (requires config)
    """

    @staticmethod
    def create_async_acp(config: AsyncACPConfig, **kwargs) -> BaseACPServer:
        """Create an async ACP instance (base or temporal)

        Args:
            config: AsyncACPConfig with type="base" or type="temporal"
            **kwargs: Additional configuration parameters
        """
        # Get implementation class
        implementation_class = ASYNC_ACP_IMPLEMENTATIONS[config.type]
        # Handle temporal-specific configuration
        if config.type == "temporal":
            # Extract temporal_address, plugins, and interceptors from config if it's a TemporalACPConfig
            temporal_config = kwargs.copy()
            if hasattr(config, "temporal_address"):
                temporal_config["temporal_address"] = config.temporal_address  # type: ignore[attr-defined]
            if hasattr(config, "plugins"):
                temporal_config["plugins"] = config.plugins  # type: ignore[attr-defined]
            if hasattr(config, "interceptors"):
                temporal_config["interceptors"] = config.interceptors  # type: ignore[attr-defined]
            return implementation_class.create(**temporal_config)
        else:
            return implementation_class.create(**kwargs)

    @staticmethod
    def locate_build_info_path() -> None:
        """If a build-info.json file is present, set the TERMINALUSE_BUILD_INFO_PATH environment variable"""
        acp_root = Path(inspect.stack()[2].filename).resolve().parents[0]
        build_info_path = acp_root / "build-info.json"
        if build_info_path.exists():
            os.environ["TERMINALUSE_BUILD_INFO_PATH"] = str(build_info_path)

    @staticmethod
    def create(
        acp_type: Literal["async"], config: BaseACPConfig | None = None, **kwargs
    ) -> BaseACPServer | AsyncBaseACP | TemporalACP:
        """Main factory method to create an async ACP

        Args:
            acp_type: Type of ACP to create (always "async")
            config: Configuration object with type="base" or type="temporal"
            **kwargs: Additional configuration parameters
        """

        FastACP.locate_build_info_path()

        if acp_type == "async":
            if config is None:
                config = AsyncACPConfig(type="base")
            if not isinstance(config, AsyncACPConfig):
                raise ValueError("AsyncACPConfig is required for async ACP type")
            return FastACP.create_async_acp(config, **kwargs)
        else:
            raise ValueError(f"Unsupported ACP type: {acp_type}")
