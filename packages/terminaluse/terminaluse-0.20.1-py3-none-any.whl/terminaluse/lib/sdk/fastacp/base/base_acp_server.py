from __future__ import annotations

import time
import uuid
import asyncio
import contextvars
import functools
from typing import Any, TypeVar, Protocol, override
from datetime import datetime
from contextlib import asynccontextmanager
from collections.abc import Callable, Awaitable

import uvicorn
from fastapi import FastAPI, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from terminaluse import AsyncTerminalUse
from terminaluse.types.task import Task
from terminaluse.lib.types.acp import (
    RPC_SYNC_METHODS,
    PARAMS_MODEL_BY_METHOD,
    RPCMethod,
    SendEventParams,
    CancelTaskParams,
    CreateTaskParams,
)
from terminaluse.lib.utils.logging import make_logger, ctx_var_request_id
from terminaluse.lib.sandbox.config import SandboxConfig, get_sandbox_config
from terminaluse.lib.sandbox.mounts import (
    Mount,
    load_config,
    assemble_sandbox_mounts,
    write_sandbox_mounts_file,
)
from terminaluse.lib.sandbox.runner import run_handler_sandboxed
from terminaluse.lib.types.json_rpc import JSONRPCError, JSONRPCRequest, JSONRPCResponse
from terminaluse.lib.adk._modules.task import TaskModule
from terminaluse.lib.utils.model_utils import BaseModel
from terminaluse.lib.types.task_context import TaskContext
from terminaluse.lib.utils.registration import register_agent
from terminaluse.lib.sandbox.handler_ref import (
    HandlerRef,
    HandlerValidationError,
    validate_handler_for_sandbox,
)

# from terminaluse.lib.sdk.fastacp.types import BaseACPConfig
from terminaluse.lib.environment_variables import EnvironmentVariables, refreshed_environment_variables
from terminaluse.lib.adk._modules.filesystem import FilesystemModule
from terminaluse.lib.sdk.fastacp.base.constants import (
    FASTACP_HEADER_SKIP_EXACT,
    FASTACP_HEADER_SKIP_PREFIXES,
)

logger = make_logger(__name__)

# Contextvar for passing assembled mounts to sandbox runner (per-request, thread-safe)
_ctx_assembled_mounts: contextvars.ContextVar[list[Mount] | None] = contextvars.ContextVar(
    "assembled_mounts", default=None
)


class ParamsWithTask(Protocol):
    """Protocol for RPC params that contain a task with filesystem_id."""

    task: Task


# TypeVar bound to ParamsWithTask for generic handler wrapping
P = TypeVar("P", bound=ParamsWithTask)


class RequestIDMiddleware:
    """Pure ASGI middleware to extract or generate request IDs.

    Uses pure ASGI (not BaseHTTPMiddleware) to preserve contextvars propagation,
    which is required for OpenTelemetry trace context to work correctly.

    See: https://www.starlette.io/middleware/#limitations
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request ID from headers (ASGI headers are list of byte tuples)
        request_id = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode("latin-1")
                break

        # Generate if not provided
        if not request_id:
            request_id = uuid.uuid4().hex

        # Set in contextvar with proper token handling
        token = ctx_var_request_id.set(request_id)
        try:
            await self.app(scope, receive, send)
        finally:
            ctx_var_request_id.reset(token)


class BaseACPServer(FastAPI):
    """
    AsyncAgentACP provides RPC-style hooks for agent events and commands asynchronously.
    All methods follow JSON-RPC 2.0 format.

    Available methods:
    - event/send → Send a message to a task
    - task/cancel → Cancel a task
    - task/approve → Approve a task
    """

    def __init__(self, sandbox_config: SandboxConfig | None = None):
        # Configure telemetry BEFORE creating FastAPI app
        # This ensures FastAPI instrumentation is set up before app initialization
        self._configure_telemetry()

        super().__init__(lifespan=self.get_lifespan_function())

        self.get("/healthz")(self._healthz)
        self.post("/api")(self._handle_jsonrpc)

        # Method handlers
        # this just adds a request ID to the request and response headers
        self.add_middleware(RequestIDMiddleware)

        self._handlers: dict[RPCMethod, Callable] = {}

        # Handler references for sandboxed execution
        self._handler_refs: dict[RPCMethod, HandlerRef] = {}

        # Sandbox configuration
        self._sandbox_config = sandbox_config or get_sandbox_config()

        # Branch ID to return in healthz (set during registration)
        self.branch_id: str | None = None

        # TerminalUse client for sync operations (created lazily)
        self._terminaluse_client: AsyncTerminalUse | None = None

        # Filesystem module for sync operations
        self._filesystem_module: FilesystemModule | None = None

        # Task module for system folder sync operations
        self._task_module: TaskModule | None = None

        # Background tasks set to prevent GC and track exceptions
        self._background_tasks: set[asyncio.Task] = set()

    def _configure_telemetry(self) -> None:
        """Configure OpenTelemetry for traces and metrics.

        Called automatically in __init__ before FastAPI initialization.
        Controlled via environment variables:
        - TERMINALUSE_TELEMETRY=false: Disable telemetry entirely
        - TERMINALUSE_AUTO_INSTRUMENT=false: Disable auto-instrumentation (manual spans only)

        Requires TERMINALUSE_BASE_URL and TERMINALUSE_AGENT_API_KEY to be set.
        """
        import os
        if os.environ.get("TERMINALUSE_TELEMETRY", "true").lower() == "false":
            logger.debug("Telemetry disabled via TERMINALUSE_TELEMETRY=false")
            return

        from terminaluse.lib.telemetry import configure_agent_telemetry

        auto_instrument = os.environ.get("TERMINALUSE_AUTO_INSTRUMENT", "true").lower() != "false"
        configure_agent_telemetry(auto_instrument=auto_instrument)

    @classmethod
    def create(cls):
        """Create and initialize BaseACPServer instance"""
        instance = cls()
        instance._setup_handlers()
        return instance

    def _setup_handlers(self):
        """Set up default handlers - override in subclasses"""
        # Base class has no default handlers
        pass

    def get_lifespan_function(self):
        @asynccontextmanager
        async def lifespan_context(app: FastAPI):  # noqa: ARG001
            env_vars = EnvironmentVariables.refresh()
            if env_vars.TERMINALUSE_BASE_URL:
                await register_agent(env_vars)
                # Store branch_id for health check responses
                self.branch_id = env_vars.TERMINALUSE_BRANCH_ID
            else:
                logger.warning("TERMINALUSE_BASE_URL not set, skipping container registration")

            yield

        return lifespan_context

    async def _healthz(self):
        """Health check endpoint - returns branch_id for platform health monitoring"""
        result = {"status": "healthy"}
        if self.branch_id:
            result["branch_id"] = self.branch_id
        return result

    def _get_terminaluse_client(self) -> AsyncTerminalUse:
        """Get or create the TerminalUse client lazily"""
        if self._terminaluse_client is None:
            env_vars = EnvironmentVariables.refresh()
            self._terminaluse_client = AsyncTerminalUse(
                base_url=env_vars.TERMINALUSE_BASE_URL if env_vars else None,
                agent_api_key=env_vars.TERMINALUSE_AGENT_API_KEY if env_vars else None,
            )
        return self._terminaluse_client

    def _get_filesystem_module(self) -> FilesystemModule:
        """Get or create the FilesystemModule lazily"""
        if self._filesystem_module is None:
            self._filesystem_module = FilesystemModule(client=self._get_terminaluse_client())
        return self._filesystem_module

    def _get_task_module(self) -> TaskModule:
        """Get or create the TaskModule lazily"""
        if self._task_module is None:
            self._task_module = TaskModule(client=self._get_terminaluse_client())
        return self._task_module


    def _wrap_with_sync(
        self,
        fn: Callable[[P], Awaitable[Any]],
        handler_name: str,
        sync_up_after: bool = False,
    ) -> Callable[[P], Awaitable[Any]]:
        """
        Wrap a handler with filesystem and system folder sync.

        Each module manages its own cache internally.
        FastACP just coordinates the sync calls and assembles mounts.
        Mounts are passed directly to the runner in memory.

        Args:
            fn: The handler function to wrap (must accept params with a task)
            handler_name: Name for logging (e.g., "on_create")
            sync_up_after: If True, also sync_up after handler completes
        """

        async def handler_with_sync(params: P) -> Any:
            handler_start = time.monotonic()

            task = params.task
            filesystem_id = task.filesystem_id
            task_id = task.id

            logger.info(f"[{handler_name}] Starting handler for task {task_id}, filesystem {filesystem_id}")

            if not task_id:
                logger.warning(f"[{handler_name}] Task has no id, skipping sync")
                return await fn(params)

            if not filesystem_id:
                logger.warning(f"[{handler_name}] Task {task_id} has no filesystem_id, skipping sync - invoking handler directly")
                return await fn(params)

            filesystem_module = self._get_filesystem_module()
            task_module = self._get_task_module()

            # Pre-sync: Download filesystem and system folders in parallel
            sync_start = time.monotonic()
            logger.info(f"[{handler_name}] Syncing down filesystem {filesystem_id} and system folder for task {task_id}")
            try:
                await asyncio.gather(
                    filesystem_module.sync_down(filesystem_id),
                    task_module.sync_down_system_folder(task_id),
                )
                sync_duration = time.monotonic() - sync_start
                logger.info(f"[{handler_name}] Sync down completed in {sync_duration:.2f}s")
            except Exception as e:
                sync_duration = time.monotonic() - sync_start
                logger.error(f"[{handler_name}] Pre-sync failed after {sync_duration:.2f}s: {e}")
                # Continue with handler even if sync fails - may be new/empty

            # Load config and assemble mounts IN MEMORY
            # Use sandbox config's agent_dir if available, otherwise default to /app
            mount_start = time.monotonic()
            agent_workdir = str(self._sandbox_config.agent_dir) if self._sandbox_config else "/app"
            agent_config = load_config(agent_workdir)
            try:
                mounts = assemble_sandbox_mounts(task_id, filesystem_id, agent_config, agent_workdir)
                write_sandbox_mounts_file(task_id, mounts)
                _ctx_assembled_mounts.set(mounts)
                mount_duration = time.monotonic() - mount_start
                logger.info(f"[{handler_name}] Mount assembly completed in {mount_duration:.2f}s")
            except Exception as e:
                logger.error(f"[{handler_name}] Failed to assemble mounts: {e}")
                _ctx_assembled_mounts.set(None)

            pre_handler_duration = time.monotonic() - handler_start
            logger.info(f"[{handler_name}] Pre-handler setup completed in {pre_handler_duration:.2f}s, invoking handler")

            if not sync_up_after:
                try:
                    return await fn(params)
                finally:
                    _ctx_assembled_mounts.set(None)

            # With sync_up_after: run handler then sync up
            try:
                return await fn(params)
            finally:
                logger.info(f"[{handler_name}] Syncing up filesystem {filesystem_id} and system folder for task {task_id}")
                sync_results = await asyncio.gather(
                    filesystem_module.sync_up(filesystem_id),
                    task_module.sync_up_system_folder(task_id),
                    return_exceptions=True,
                )
                for i, sync_result in enumerate(sync_results):
                    if isinstance(sync_result, Exception):
                        sync_name = "filesystem" if i == 0 else "system_folder"
                        logger.error(f"[{handler_name}] Post-sync failed for {sync_name}: {sync_result}")
                _ctx_assembled_mounts.set(None)

        return handler_with_sync

    def _should_sandbox(self, method: RPCMethod) -> bool:
        """Check if a method should be executed in a sandbox."""
        return method in self._handler_refs

    def _wrap_with_maybe_sandbox(
        self,
        fn: Callable[[P], Awaitable[Any]],
        method: RPCMethod,
    ) -> Callable[[P], Awaitable[Any]]:
        """Wrap a handler to run sandboxed or in-process based on config."""

        async def maybe_sandboxed(params: P) -> Any:
            if self._should_sandbox(method):
                return await self._run_sandboxed_handler(method, params)  # type: ignore[arg-type]
            return await fn(params)

        return maybe_sandboxed

    async def _run_sandboxed_handler(
        self,
        method: RPCMethod,
        params: BaseModel,
    ) -> None:
        """Run a handler in a sandbox."""
        handler_ref = self._handler_refs[method]
        task = getattr(params, "task", None)
        task_id = getattr(task, "id", None)
        mounts = _ctx_assembled_mounts.get()

        logger.info(f"Running handler in sandbox: {handler_ref.module}.{handler_ref.function}")
        if mounts:
            logger.info(f"Passing {len(mounts)} mounts to sandbox")

        result = await run_handler_sandboxed(
            method=method.value,
            handler_ref=handler_ref,
            params=params,
            mounts=mounts,
            task_id=task_id,
        )

        # Log result - no truncation, full output is valuable for debugging sandbox issues
        if result.success:
            logger.info(f"Sandboxed handler completed: {handler_ref.module}.{handler_ref.function}")
            if result.stderr:
                logger.warning(f"Sandbox stderr (handler succeeded): {result.stderr}")
        else:
            logger.error(
                f"Sandboxed handler failed: {handler_ref.module}.{handler_ref.function}, "
                f"exit_code={result.exit_code}, timed_out={result.timed_out}"
            )
            if result.stdout:
                logger.error(f"Sandbox stdout: {result.stdout}")
            if result.stderr:
                logger.error(f"Sandbox stderr: {result.stderr}")

    async def _handle_jsonrpc(self, request: Request):
        """Main JSON-RPC endpoint handler"""
        rpc_request = None
        logger.info(f"[base_acp_server] received request: {datetime.now()}")
        try:
            data = await request.json()
            rpc_request = JSONRPCRequest(**data)

            # Check if the request is authenticated
            if refreshed_environment_variables and getattr(refreshed_environment_variables, "TERMINALUSE_AGENT_API_KEY", None):
                authorization_header = request.headers.get("x-agent-api-key")
                if authorization_header != refreshed_environment_variables.TERMINALUSE_AGENT_API_KEY:
                    return JSONRPCResponse(
                        id=rpc_request.id,
                        error=JSONRPCError(code=-32601, message="Unauthorized"),
                    )

            # Check if method is valid first
            try:
                method = RPCMethod(rpc_request.method)
            except ValueError:
                logger.error(f"Method {rpc_request.method} was invalid")
                return JSONRPCResponse(
                    id=rpc_request.id,
                    error=JSONRPCError(code=-32601, message=f"Method {rpc_request.method} not found"),
                )

            if method not in self._handlers or self._handlers[method] is None:
                logger.error(f"Method {method} not found on existing ACP server")
                return JSONRPCResponse(
                    id=rpc_request.id,
                    error=JSONRPCError(code=-32601, message=f"Method {method} not found"),
                )

            # Extract application headers using allowlist approach (only x-* headers)
            # Matches gateway's security filtering rules
            # Forward filtered headers via params.request.headers to agent handlers
            custom_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower().startswith("x-")
                and key.lower() not in FASTACP_HEADER_SKIP_EXACT
                and not any(key.lower().startswith(p) for p in FASTACP_HEADER_SKIP_PREFIXES)
            }

            # Parse params into appropriate model based on method and include headers
            params_model = PARAMS_MODEL_BY_METHOD[method]
            params_data = dict(rpc_request.params) if rpc_request.params else {}

            # Add custom headers to the request structure if any headers were provided
            # Gateway sends filtered headers via HTTP, SDK extracts and populates params.request
            if custom_headers:
                params_data["request"] = {"headers": custom_headers}
            params = params_model.model_validate(params_data)

            if method in RPC_SYNC_METHODS:
                handler = self._handlers[method]
                result = await handler(params)

                if rpc_request.id is None:
                    # Seems like you should return None for notifications
                    return None
                else:
                    if isinstance(result, BaseModel):
                        result = result.model_dump()
                    return JSONRPCResponse(id=rpc_request.id, result=result)
            else:
                # Capture current context (includes trace context from incoming request)
                ctx = contextvars.copy_context()

                if rpc_request.id is None:
                    task = asyncio.create_task(self._process_notification(method, params), context=ctx)
                    self._track_background_task(task)
                    return JSONRPCResponse(id=None)

                task = asyncio.create_task(self._process_request(rpc_request.id, method, params), context=ctx)
                self._track_background_task(task)
                return JSONRPCResponse(id=rpc_request.id, result={"status": "processing"})

        except Exception as e:
            logger.error(f"Error handling JSON-RPC request: {e}", exc_info=True)
            request_id = None
            if rpc_request is not None:
                request_id = rpc_request.id
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(code=-32603, message=str(e)),
            )

    async def _process_notification(self, method: RPCMethod, params: Any):
        """Process a notification (request with no ID) in the background"""
        start = time.monotonic()
        logger.info(f"[base_acp_server] Background task started for notification {method}")
        try:
            await self._handlers[method](params)
            duration = time.monotonic() - start
            logger.info(f"[base_acp_server] Notification {method} completed in {duration:.2f}s")
        except Exception as e:
            logger.error(f"Error processing notification {method}: {e}", exc_info=True)

    async def _process_request(self, request_id: int | str, method: RPCMethod, params: Any):
        """Process a request in the background"""
        start = time.monotonic()
        logger.info(f"[base_acp_server] Background task started for request {request_id} method {method}")
        try:
            await self._handlers[method](params)
            duration = time.monotonic() - start
            logger.info(f"Successfully processed request {request_id} for method {method} in {duration:.2f}s")
        except Exception as e:
            duration = time.monotonic() - start
            logger.error(
                f"Error processing request {request_id} for method {method} after {duration:.2f}s: {e}",
                exc_info=True,
            )

    def _track_background_task(self, task: asyncio.Task) -> None:
        """Track a background task to prevent GC and log uncaught exceptions.

        Adds the task to the internal set to keep a strong reference (preventing
        garbage collection), and registers a done callback to:
        1. Remove the task from the set when it completes
        2. Log any uncaught exceptions that weren't handled in the task itself

        This ensures fire-and-forget tasks don't silently swallow exceptions.
        """
        self._background_tasks.add(task)

        def _on_task_done(t: asyncio.Task) -> None:
            self._background_tasks.discard(t)
            # Check for exceptions that weren't raised/handled within the task
            if not t.cancelled():
                exc = t.exception()
                if exc is not None:
                    logger.error(
                        f"Uncaught exception in background task {t.get_name()}: {exc}",
                        exc_info=(type(exc), exc, exc.__traceback__),
                    )

        task.add_done_callback(_on_task_done)

    """
    Define all possible decorators to be overriden and implemented by each ACP implementation
    Then the users can override the default handlers by implementing their own handlers

    ACP Type: Async
    Decorators:
    - on_create
    - on_event
    - on_cancel
    """

    def _register_handler(
        self,
        fn: Callable[..., Awaitable[Any]],
        method: RPCMethod,
        handler_name: str,
        sync_up_after: bool = False,
        skip_sync: bool = False,
    ) -> None:
        """Internal handler registration with sandboxing and sync wrapping.

        Args:
            fn: The handler function to register
            method: The RPC method to register the handler for
            handler_name: Name for logging (e.g., "on_create")
            sync_up_after: If True, sync filesystem up after handler completes
            skip_sync: If True, skip filesystem sync entirely (e.g., for cancel)
        """
        # Register for sandboxing
        try:
            handler_ref = validate_handler_for_sandbox(fn)
            self._handler_refs[method] = handler_ref
            logger.info(f"Handler registered for sandboxing: {handler_ref.module}.{handler_ref.function}")
        except HandlerValidationError as e:
            logger.warning(f"Handler not suitable for sandboxing, will run in-process: {e}")

        maybe_sandboxed = self._wrap_with_maybe_sandbox(fn, method)

        if skip_sync:
            self._handlers[method] = maybe_sandboxed
        else:
            self._handlers[method] = self._wrap_with_sync(
                maybe_sandboxed, handler_name=handler_name, sync_up_after=sync_up_after
            )

    # ==========================================================================
    # TaskContext-based decorators (public API)
    # ==========================================================================

    def on_create(self, fn: Callable[..., Awaitable[Any]]):
        """Handle task/create with TaskContext injection.

        The decorated function receives:
        - ctx: TaskContext with pre-bound task/agent IDs and module wrappers
        - params: dict[str, Any] containing the user-provided parameters

        Example:
            @server.on_create
            async def handle_create(ctx: TaskContext, params: dict[str, Any]):
                agent_type = params.get("agent_type")
                await ctx.state.create(state={"agent_type": agent_type})
                await ctx.reply("Task created!")
        """

        @functools.wraps(fn)
        async def with_context(params: CreateTaskParams):
            ctx = TaskContext(task=params.task, agent=params.agent, request=params.request)
            return await fn(ctx, params.params or {})

        self._register_handler(
            with_context,
            RPCMethod.TASK_CREATE,
            handler_name="on_create",
            sync_up_after=False,
        )
        return fn

    @override  # Intentionally shadows FastAPI's deprecated on_event lifecycle decorator
    def on_event(self, fn: Callable[..., Awaitable[Any]]):  # type: ignore[override]
        """Handle event/send with TaskContext injection.

        The decorated function receives:
        - ctx: TaskContext with pre-bound task/agent IDs and module wrappers
        - event: Event object containing the incoming event data

        Example:
            @server.on_event
            async def handle_event(ctx: TaskContext, event: Event):
                await ctx.reply(f"Received: {event.content}")
        """

        @functools.wraps(fn)
        async def with_context(params: SendEventParams):
            ctx = TaskContext(task=params.task, agent=params.agent, request=params.request)
            return await fn(ctx, params.event)

        self._register_handler(
            with_context,
            RPCMethod.EVENT_SEND,
            handler_name="on_event",
            sync_up_after=True,
        )
        return fn

    def on_cancel(self, fn: Callable[..., Awaitable[Any]]):
        """Handle task/cancel with TaskContext injection.

        The decorated function receives:
        - ctx: TaskContext with pre-bound task/agent IDs and module wrappers

        Example:
            @server.on_cancel
            async def handle_cancel(ctx: TaskContext):
                await ctx.reply("Task cancelled")
        """

        @functools.wraps(fn)
        async def with_context(params: CancelTaskParams):
            ctx = TaskContext(task=params.task, agent=params.agent, request=params.request)
            return await fn(ctx)

        self._register_handler(
            with_context,
            RPCMethod.TASK_CANCEL,
            handler_name="on_cancel",
            skip_sync=True,
        )
        return fn

    """
    End of Decorators
    """

    """
    ACP Server Lifecycle Methods
    """

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Start the Uvicorn server for async handlers."""
        uvicorn.run(self, host=host, port=port, **kwargs)
