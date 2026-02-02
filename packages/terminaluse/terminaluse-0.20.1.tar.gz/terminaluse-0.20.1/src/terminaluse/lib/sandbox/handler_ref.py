"""Handler reference derivation and validation for sandboxed execution."""

from __future__ import annotations

import inspect
from typing import Any, Callable
from dataclasses import dataclass


@dataclass
class HandlerRef:
    """Reference to a handler that can be imported in the jail."""

    module: str
    function: str

    def to_dict(self) -> dict[str, str]:
        return {"module": self.module, "function": self.function}


class HandlerValidationError(TypeError):
    """Raised when a handler is not suitable for sandboxed execution."""

    pass


def handler_ref_from_callable(fn: Callable[..., Any]) -> HandlerRef:
    """
    Derive handler reference from a callable.

    The handler must be:
    - A real function object (not a lambda, closure, or callable class)
    - Defined at module scope (top-level)
    - Have valid __module__ and __name__ attributes

    Args:
        fn: The handler function to derive reference from

    Returns:
        HandlerRef with module and function name

    Raises:
        HandlerValidationError: If the handler cannot be safely imported in a jail
    """
    # Must be a real function object
    if not inspect.isfunction(fn):
        raise HandlerValidationError(f"Sandboxed handlers must be module-level functions, got {type(fn).__name__}")

    # Disallow lambdas
    if fn.__name__ == "<lambda>":
        raise HandlerValidationError("Sandboxed handlers cannot be lambdas (no stable import path)")

    # Disallow nested/local functions (contain <locals> in qualname)
    if "<locals>" in fn.__qualname__:
        raise HandlerValidationError(
            f"Sandboxed handlers must be top-level functions, got nested function: {fn.__qualname__}"
        )

    # Must have valid module and name
    module = fn.__module__
    name = fn.__name__

    if not module:
        raise HandlerValidationError(f"Handler {fn} has no __module__ attribute")

    if not name:
        raise HandlerValidationError(f"Handler {fn} has no __name__ attribute")

    # Reject built-in module (would indicate something weird)
    if module == "builtins":
        raise HandlerValidationError(f"Handler {name} appears to be a builtin, not a user-defined function")

    return HandlerRef(module=module, function=name)


def validate_handler_for_sandbox(fn: Callable[..., Any]) -> HandlerRef:
    """
    Validate a handler for sandbox execution and return its reference.

    This should be called at registration time (when the decorator runs).

    Args:
        fn: The handler function

    Returns:
        HandlerRef if valid

    Raises:
        HandlerValidationError: If the handler is not suitable for sandboxing
    """
    return handler_ref_from_callable(fn)
