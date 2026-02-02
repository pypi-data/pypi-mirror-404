"""
Sandboxed handler entrypoint - runs inside bubblewrap sandbox.

Protocol:
  stdin:  JSON object with keys: method, handler, params
  stdout: Small status object as JSON (optional)
  stderr: All logging output (captured by runner)
  exit 0: success
  exit 1: failure
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import sys
from typing import Any, Callable


class _StructuredLogFormatter(logging.Formatter):
    """JSON log formatter for structured log output.

    Outputs logs as JSON with separate fields for timestamp, level, logger, and message.
    This allows the LogSender to extract metadata without parsing text prefixes.
    """

    def format(self, record: logging.LogRecord) -> str:
        from datetime import datetime, timezone

        msg = record.getMessage()

        # Include exception traceback in the message (if present)
        # This ensures logger.exception() produces a single JSON log entry
        # with the full traceback, rather than losing it.
        if record.exc_info and isinstance(record.exc_info, tuple) and record.exc_info[1] is not None:
            exc_text = self.formatException(record.exc_info)
            msg = f"{msg}\n{exc_text}"
        elif record.exc_text:
            msg = f"{msg}\n{record.exc_text}"

        if record.stack_info:
            msg = f"{msg}\n{record.stack_info}"

        return json.dumps(
            {
                "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "msg": msg,
            },
            separators=(",", ":"),
        )


def _configure_logging() -> None:
    """Configure logging to stderr for sandbox environment.

    All logs go to stderr so they can be captured by the sandbox runner.
    Uses JSON format for structured log parsing by LogSender.
    The log level is controlled by TERMINALUSE_LOG_LEVEL (default: INFO).
    """
    log_level = os.getenv("TERMINALUSE_LOG_LEVEL", "INFO").upper()

    # Configure root logger with JSON formatter
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_StructuredLogFormatter())

    # Clear any existing handlers and set up fresh
    logging.root.handlers = []
    logging.root.addHandler(handler)
    logging.root.setLevel(getattr(logging, log_level, logging.INFO))


def _get_params_class(method: str):
    """Get the appropriate params class for a method."""
    # Import here to ensure it works in the jail
    from terminaluse.lib.types.acp import (
        CancelTaskParams,
        CreateTaskParams,
        SendEventParams,
    )

    method_to_class = {
        "task/create": CreateTaskParams,
        "event/send": SendEventParams,
        "task/cancel": CancelTaskParams,
    }

    cls = method_to_class.get(method)
    if cls is None:
        raise ValueError(f"Unsupported method: {method}")
    return cls


def _load_params(method: str, data: dict[str, Any]):
    """Load and validate params for the given method."""
    params_data = data.get("params", {})
    params_class = _get_params_class(method)
    return params_class.model_validate(params_data)


def _invoke_handler(method: str, params: Any, fn: Callable[..., Any]) -> None:
    """
    Invoke handler with TaskContext injection based on method type.

    The handler signatures are:
    - task/create: fn(ctx: TaskContext, params: dict[str, Any])
    - event/send: fn(ctx: TaskContext, event: Event)
    - task/cancel: fn(ctx: TaskContext)
    """
    from terminaluse.lib.types.task_context import TaskContext

    # Create TaskContext from params (all methods have task, agent, request)
    ctx = TaskContext(task=params.task, agent=params.agent, request=params.request)

    # Type annotation to handle different tuple lengths for each method
    args: tuple[TaskContext] | tuple[TaskContext, Any]
    if method == "task/create":
        args = (ctx, params.params or {})
    elif method == "event/send":
        args = (ctx, params.event)
    elif method == "task/cancel":
        args = (ctx,)
    else:
        raise ValueError(f"Unsupported method: {method}")

    if asyncio.iscoroutinefunction(fn):
        asyncio.run(fn(*args))
    else:
        fn(*args)


def _load_handler(handler_ref: dict[str, str]) -> Callable[..., Any]:
    """
    Load a user handler by import path.

    The handler must be importable inside the jail and use the TaskContext-based signature:
    - on_create: fn(ctx: TaskContext, params: dict[str, Any])
    - on_event: fn(ctx: TaskContext, event: Event)
    - on_cancel: fn(ctx: TaskContext)
    """
    module_name = handler_ref.get("module")
    function_name = handler_ref.get("function")

    if not module_name or not function_name:
        raise ValueError("handler.module and handler.function are required")

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ValueError(f"Could not import handler module: {module_name}") from e

    fn = getattr(module, function_name, None)
    if fn is None:
        raise ValueError(f"Handler not found: {module_name}.{function_name}")

    if not callable(fn):
        raise ValueError(f"Handler is not callable: {module_name}.{function_name}")

    return fn


def main() -> int:
    """Main entrypoint for jailed handler execution."""
    import time

    t_start = time.perf_counter()

    # Configure logging first so all handler logs go to stderr
    _configure_logging()
    logger = logging.getLogger(__name__)

    t_logging = time.perf_counter()

    try:
        logger.info(f"[TIMING] sandbox_entrypoint_start: {(t_logging - t_start)*1000:.0f}ms (logging setup)")

        # Read payload from stdin
        raw = sys.stdin.read()
        if not raw:
            raise ValueError("No input received on stdin")

        payload = json.loads(raw)
        t_payload = time.perf_counter()
        logger.info(f"[TIMING] payload_read: {(t_payload - t_logging)*1000:.0f}ms")

        # Extract and validate
        method = payload.get("method")
        if not method:
            raise ValueError("Missing 'method' in payload")

        handler_ref = payload.get("handler", {})
        if not handler_ref:
            raise ValueError("Missing 'handler' in payload")

        logger.info(f"Invoking handler: {handler_ref.get('module')}.{handler_ref.get('function')} for method={method}")

        # Load params and handler
        t_before_params = time.perf_counter()
        params = _load_params(method, payload)
        t_after_params = time.perf_counter()
        logger.info(f"[TIMING] load_params: {(t_after_params - t_before_params)*1000:.0f}ms")

        fn = _load_handler(handler_ref)
        t_after_handler_load = time.perf_counter()
        logger.info(f"[TIMING] load_handler (imports): {(t_after_handler_load - t_after_params)*1000:.0f}ms")

        # Execute handler with TaskContext injection
        _invoke_handler(method, params, fn)
        t_after_invoke = time.perf_counter()

        logger.info(f"[TIMING] handler_execution: {(t_after_invoke - t_after_handler_load)*1000:.0f}ms")
        logger.info(f"[TIMING] total_sandbox_time: {(t_after_invoke - t_start)*1000:.0f}ms")
        logger.info("Handler completed successfully")

        # Success - write status to stdout
        out = {"status": "ok"}
        sys.stdout.write(json.dumps(out))
        return 0

    except Exception as exc:
        # Log full exception with traceback
        logger.exception(f"Sandboxed handler failed: {exc}")

        # Try to write error status to stdout (ACP wrapper may use this)
        try:
            error_out = {"status": "error", "error": str(exc)}
            sys.stdout.write(json.dumps(error_out))
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
