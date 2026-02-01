from __future__ import annotations

from typing import Any, override

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer

logger = make_logger(__name__)


class SyncACP(BaseACPServer):
    """
    SyncACP provides synchronous request-response style communication.
    Handlers execute and return responses immediately.

    Note: The message/send functionality has been deprecated.
    Use event/send for asynchronous communication instead.
    """

    def __init__(self):
        super().__init__()
        self._setup_handlers()

    @classmethod
    @override
    def create(cls, **kwargs: Any) -> "SyncACP":
        """Create and initialize SyncACP instance

        Args:
            **kwargs: Configuration parameters (unused in sync implementation)

        Returns:
            Initialized SyncACP instance
        """
        logger.info("Creating SyncACP instance")
        instance = cls()
        logger.info("SyncACP instance created")
        return instance

    @override
    def _setup_handlers(self):
        """Set up default handlers for sync operations"""
        # No default handlers - message/send has been deprecated
        pass
