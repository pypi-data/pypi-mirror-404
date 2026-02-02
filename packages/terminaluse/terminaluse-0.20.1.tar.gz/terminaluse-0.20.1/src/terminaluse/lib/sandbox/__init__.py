"""
Sandbox module for bubblewrap-based handler isolation.

This module provides sandboxing capabilities for async handler execution,
isolating each handler invocation in its own bubblewrap sandbox.

bubblewrap is used instead of nsjail because nsjail requires prctl(PR_SET_SECUREBITS)
which gVisor hasn't implemented. bubblewrap provides equivalent filesystem isolation
and works correctly inside gVisor (GKE Sandbox).
"""

from terminaluse.lib.sandbox.config import SandboxConfig, configure_sandbox, get_sandbox_config
from terminaluse.lib.sandbox.runner import (
    SandboxResult,
    SandboxRunner,
    get_sandbox_runner,
    run_handler_sandboxed,
)
from terminaluse.lib.sandbox.handler_ref import (
    HandlerRef,
    HandlerValidationError,
    handler_ref_from_callable,
    validate_handler_for_sandbox,
)

__all__ = [
    # Config
    "SandboxConfig",
    "get_sandbox_config",
    "configure_sandbox",
    # Handler reference
    "HandlerRef",
    "HandlerValidationError",
    "handler_ref_from_callable",
    "validate_handler_for_sandbox",
    # Runner
    "SandboxResult",
    "SandboxRunner",
    "get_sandbox_runner",
    "run_handler_sandboxed",
]
