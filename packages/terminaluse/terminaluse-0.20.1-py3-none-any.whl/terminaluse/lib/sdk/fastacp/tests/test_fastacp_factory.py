from unittest.mock import MagicMock, patch

import pytest

from terminaluse.lib.types.fastacp import (
    AsyncACPConfig,
    TemporalACPConfig,
    AsyncBaseACPConfig,
)
from terminaluse.lib.sdk.fastacp.fastacp import FastACP
from terminaluse.lib.sdk.fastacp.impl.temporal_acp import TemporalACP
from terminaluse.lib.sdk.fastacp.impl.async_base_acp import AsyncBaseACP
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer


class TestFastACPInitialization:
    """Test FastACP basic functionality"""

    def test_factory_class_exists(self):
        """Test that FastACP class exists and is properly structured"""
        assert hasattr(FastACP, "create")
        assert hasattr(FastACP, "create_async_acp")


class TestAsyncBaseACPCreation:
    """Test AsyncBaseACP creation through factory"""

    @pytest.mark.asyncio
    async def test_create_async_base_acp_direct_method(self):
        """Test creating AsyncBaseACP using direct method"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="base")
            async_acp = FastACP.create_async_acp(config=config)

            assert isinstance(async_acp, AsyncBaseACP)
            assert isinstance(async_acp, BaseACPServer)

    @pytest.mark.asyncio
    async def test_create_async_base_acp_with_specific_config(self):
        """Test creating AsyncBaseACP with AsyncBaseACPConfig"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncBaseACPConfig(type="base")
            async_acp = FastACP.create_async_acp(config=config)

            assert isinstance(async_acp, AsyncBaseACP)

    @pytest.mark.asyncio
    async def test_create_async_base_acp_via_generic_create(self):
        """Test creating AsyncBaseACP via generic create method"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="base")
            async_acp = FastACP.create("async", config=config)

            assert isinstance(async_acp, AsyncBaseACP)

    @pytest.mark.asyncio
    async def test_create_async_base_acp_default_config(self):
        """Test creating AsyncBaseACP with default config when none provided"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            async_acp = FastACP.create("async")

            assert isinstance(async_acp, AsyncBaseACP)


class TestAsyncTemporalACPCreation:
    """Test AsyncTemporalACP (TemporalACP) creation through factory"""

    @pytest.mark.asyncio
    async def test_create_temporal_acp_direct_method(self):
        """Test creating TemporalACP using direct method"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="temporal")

            # Mock the TemporalACP.create method since it requires temporal dependencies
            with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_create.return_value = mock_temporal_instance

                temporal_acp = FastACP.create_async_acp(config=config)

                assert temporal_acp == mock_temporal_instance
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_temporal_acp_with_temporal_config(self):
        """Test creating TemporalACP with TemporalACPConfig"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = TemporalACPConfig(type="temporal", temporal_address="localhost:7233")

            with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_create.return_value = mock_temporal_instance

                temporal_acp = FastACP.create_async_acp(config=config)

                assert temporal_acp == mock_temporal_instance
                # Verify temporal_address was passed
                mock_create.assert_called_once_with(
                    temporal_address="localhost:7233",
                    plugins=[],
                    interceptors=[],
                )

    @pytest.mark.asyncio
    async def test_create_temporal_acp_via_generic_create(self):
        """Test creating TemporalACP via generic create method"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="temporal")

            with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_create.return_value = mock_temporal_instance

                temporal_acp = FastACP.create("async", config=config)

                assert temporal_acp == mock_temporal_instance

    @pytest.mark.asyncio
    async def test_create_temporal_acp_with_custom_address(self):
        """Test creating TemporalACP with custom temporal address"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = TemporalACPConfig(type="temporal", temporal_address="custom-temporal:9999")

            with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_create.return_value = mock_temporal_instance

                FastACP.create_async_acp(config=config)

                mock_create.assert_called_once_with(
                    temporal_address="custom-temporal:9999",
                    plugins=[],
                    interceptors=[],
                )


class TestConfigurationValidation:
    """Test configuration validation and error handling"""

    @pytest.mark.asyncio
    async def test_async_direct_method_requires_config(self):
        """Test that direct async method requires configuration"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            # This should raise TypeError since config is required parameter
            with pytest.raises(TypeError):
                FastACP.create_async_acp()  # type: ignore[call-arg]

    def test_invalid_async_type_in_config(self):
        """Test that invalid async type in config raises ValueError"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            # This should raise ValueError during config creation
            with pytest.raises(ValueError):
                AsyncACPConfig(type="invalid_async_type")


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_async_acp_creation_failure(self):
        """Test handling of AsyncACP creation failure"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="base")

            with patch.object(AsyncBaseACP, "create", side_effect=Exception("Creation failed")):
                with pytest.raises(Exception, match="Creation failed"):
                    FastACP.create_async_acp(config=config)

    @pytest.mark.asyncio
    async def test_temporal_acp_creation_failure(self):
        """Test handling of TemporalACP creation failure"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            config = AsyncACPConfig(type="temporal")

            with patch.object(TemporalACP, "create", side_effect=Exception("Temporal connection failed")):
                with pytest.raises(Exception, match="Temporal connection failed"):
                    FastACP.create_async_acp(config=config)


class TestIntegrationScenarios:
    """Test integration scenarios and real-world usage patterns"""

    @pytest.mark.asyncio
    async def test_create_all_async_acp_types(self):
        """Test creating all supported async ACP types"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            # Create AsyncBaseACP
            base_config = AsyncACPConfig(type="base")
            async_base = FastACP.create("async", config=base_config)
            assert isinstance(async_base, AsyncBaseACP)

            # Create TemporalACP (mocked)
            temporal_config = AsyncACPConfig(type="temporal")
            with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_create.return_value = mock_temporal_instance

                temporal_acp = FastACP.create("async", config=temporal_config)
                assert temporal_acp == mock_temporal_instance

    @pytest.mark.asyncio
    async def test_configuration_driven_creation(self):
        """Test configuration-driven ACP creation"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            configs = [
                ("async", AsyncACPConfig(type="base")),
                ("async", TemporalACPConfig(type="temporal", temporal_address="localhost:7233")),
            ]

            created_acps = []

            for acp_type, config in configs:
                if config.type == "temporal":
                    # Mock temporal creation
                    with patch.object(TemporalACP, "create", new_callable=MagicMock) as mock_create:
                        mock_temporal_instance = MagicMock(spec=TemporalACP)
                        mock_create.return_value = mock_temporal_instance

                        acp = FastACP.create(acp_type, config=config)
                        created_acps.append(acp)
                else:
                    acp = FastACP.create(acp_type, config=config)
                    created_acps.append(acp)

            assert len(created_acps) == 2
            assert isinstance(created_acps[0], AsyncBaseACP)
            # Second one is mocked TemporalACP

    @pytest.mark.asyncio
    async def test_factory_with_custom_kwargs(self):
        """Test factory methods with custom keyword arguments"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            # Test async base with kwargs
            config = AsyncACPConfig(type="base")
            async_acp = FastACP.create_async_acp(config=config, custom_param="test")
            assert isinstance(async_acp, AsyncBaseACP)
