"""Subprocess spawning and bubblewrap invocation for sandboxed handlers."""

from __future__ import annotations

import json
import time
import asyncio
import os
import subprocess
from typing import Any
from pathlib import Path
from dataclasses import dataclass

from pydantic import BaseModel

from opentelemetry import trace

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.sandbox.config import SandboxConfig, get_sandbox_config
from terminaluse.lib.sandbox.handler_ref import HandlerRef
from terminaluse.lib.sandbox.mounts import Mount, configure_bwrap_mounts

logger = make_logger(__name__)


@dataclass
class SandboxResult:
    """Result of a sandboxed handler invocation."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def status_json(self) -> dict[str, Any] | None:
        """Parse stdout as JSON status, or None if invalid."""
        if not self.stdout.strip():
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            return None


class SandboxRunner:
    """Runs handlers in bubblewrap sandboxes.

    bubblewrap is used instead of nsjail because nsjail requires prctl(PR_SET_SECUREBITS)
    which gVisor hasn't implemented. bubblewrap provides equivalent filesystem isolation
    and works correctly inside gVisor (GKE Sandbox).
    """

    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or get_sandbox_config()

    def _build_bwrap_command(self, mounts: list[Mount] | None = None) -> list[str]:
        """Build the bubblewrap command with all arguments.

        Args:
            mounts: Pre-assembled list of mounts (filesystem, system folders, baked).
                   If None, creates ephemeral tmpfs at /workspace and /root/.claude.

        Note: bubblewrap doesn't have built-in timeout like nsjail's --time_limit.
        The timeout is applied by wrapping with the `timeout` command in run().
        """
        config = self.config

        cmd = [config.bwrap_path]

        # Namespace isolation
        # --unshare-user: Create new user namespace (unprivileged isolation)
        # --unshare-pid: Create new PID namespace (process isolation)
        # --unshare-ipc: Create new IPC namespace (shared memory isolation)
        # Note: We keep network shared (--share-net) for LLM API calls
        cmd.extend([
            "--unshare-user",
            "--unshare-pid",
            "--unshare-ipc",
            "--share-net",  # Keep network for LLM API calls
        ])

        # Process lifecycle
        cmd.extend([
            "--die-with-parent",  # Kill sandbox when parent dies
        ])

        # /proc access: Use bind-mount instead of fresh procfs
        # Fresh procfs (--proc /proc) fails in Docker because it requires
        # additional privileges. Bind-mounting works like nsjail did.
        # Note: In gVisor this is fine since gVisor handles all syscalls.
        cmd.extend(["--ro-bind", "/proc", "/proc"])

        # /dev: Create minimal /dev with essential devices
        cmd.extend(["--dev", "/dev"])

        # Read-only system mounts
        cmd.extend([
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/bin", "/bin",
        ])

        # DNS, SSL, and hostname resolution
        cmd.extend([
            "--ro-bind", "/etc/resolv.conf", "/etc/resolv.conf",
            "--ro-bind", "/etc/ssl", "/etc/ssl",
            "--ro-bind", "/etc/hosts", "/etc/hosts",
        ])

        # Dynamic linker configuration (needed for Python shared libs)
        if Path("/etc/ld.so.cache").exists():
            cmd.extend(["--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache"])

        # Agent code (read-only)
        # Mount code subdir (e.g., "project") to /agent/<subdir>
        cmd.extend([
            "--ro-bind",
            f"{config.agent_dir}/{config.code_subdir}",
            f"/agent/{config.code_subdir}",
        ])

        # Ephemeral /tmp (cleared after each task)
        cmd.extend(["--tmpfs", "/tmp"])

        # Writable home directory for subprocesses (e.g., Claude CLI uses ~/.claude)
        # Must come before any /root/.claude mounts so they overlay correctly
        cmd.extend(["--tmpfs", "/root"])

        # Dynamic mounts: filesystem, system folders, and baked mounts
        if mounts:
            # Use configure_bwrap_mounts to generate mount args in correct order
            cmd.extend(configure_bwrap_mounts(mounts))
        else:
            # No mounts provided: create ephemeral tmpfs at /workspace
            cmd.extend(["--tmpfs", "/workspace"])

        # Add /lib64 if it exists (varies by distro)
        if Path("/lib64").exists():
            cmd.extend(["--ro-bind", "/lib64", "/lib64"])

        # Add /sbin if it exists
        if Path("/sbin").exists():
            cmd.extend(["--ro-bind", "/sbin", "/sbin"])

        # Mount /app/src if it exists (for editable/development installs of terminaluse)
        if Path("/app/src").exists():
            cmd.extend(["--ro-bind", "/app/src", "/app/src"])

        return cmd

    def _build_env_args(self, extra_env: dict[str, str] | None = None) -> list[str]:
        """Build environment variable arguments for bubblewrap.

        Environment variables are applied in order, with later values overriding earlier:
        1. Parent process env vars (includes user-defined vars from `tu env`)
        2. System env vars (PYTHONPATH, PATH, etc.)
        3. Platform env vars from EnvironmentVariables
        4. Invocation-specific extra_env

        Note: bubblewrap uses --clearenv to start with empty environment,
        then --setenv to add specific variables (unlike nsjail's --env KEY=VALUE).
        """
        env_args = ["--clearenv"]  # Start with clean environment

        # Collect all env vars in order (later values override earlier)
        all_env: dict[str, str] = {}

        # 1. Pass through all env vars from parent process
        # This includes user-defined vars set via `tu env add`
        for key, value in os.environ.items():
            all_env[key] = value

        # 2. System env vars (override parent values)
        # Uses system Python (installed via uv pip install --system in Dockerfile)
        system_env = {
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": "/agent:/usr/local/lib/python3.12/site-packages",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/usr/local/lib:/usr/lib:/lib",
            "HOME": "/root",  # Needed for subprocesses like Claude CLI (~/.claude)
            # Disable io_uring to avoid hangs on certain kernel versions (6.6.57-6.6.59)
            # See: https://github.com/nodejs/node/issues/51875
            "UV_USE_IO_URING": "0",
            # Limit Node.js/V8 heap size to reduce memory usage for Claude CLI
            # Default V8 heap can grow to 1.5GB+; limit to 512MB to fit in constrained pods
            "NODE_OPTIONS": "--max-old-space-size=512",
            # Tell Claude CLI we're running inside a sandbox, allowing --dangerously-skip-permissions
            # to work even as root. This is the official escape hatch for sandboxed environments.
            # See: https://github.com/anthropics/claude-code/issues/9184
            "IS_SANDBOX": "1",
        }
        all_env.update(system_env)

        # 3. Platform env vars from EnvironmentVariables (override parent values)
        from terminaluse.lib.environment_variables import EnvironmentVariables

        env_vars = EnvironmentVariables.refresh()
        for field_name, value in env_vars.model_dump().items():
            if value is not None:
                all_env[field_name] = str(value)  # Ensure string for bwrap --setenv

        # 4. Extra env vars for this specific invocation
        if extra_env:
            all_env.update(extra_env)

        # Convert to bubblewrap format: --setenv KEY VALUE
        for key, value in all_env.items():
            env_args.extend(["--setenv", key, value])

        return env_args

    def run(
        self,
        method: str,
        handler_ref: HandlerRef,
        params: BaseModel,
        mounts: list[Mount] | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> SandboxResult:
        """
        Run a handler in a bubblewrap sandbox.

        Args:
            method: The JSON-RPC method name (e.g., "event/send")
            handler_ref: Reference to the handler to run
            params: The Pydantic params model to pass to the handler
            mounts: Pre-assembled list of mounts (filesystem, system folders, baked)
            extra_env: Additional environment variables for this invocation

        Returns:
            SandboxResult with execution outcome
        """
        config = self.config

        # Build the payload
        payload = {
            "method": method,
            "params_type": type(params).__name__,
            "handler": handler_ref.to_dict(),
            "params": params.model_dump(mode="json"),
        }
        payload_json = json.dumps(payload)

        # Build the bubblewrap command
        bwrap_cmd = self._build_bwrap_command(mounts=mounts)
        bwrap_cmd.extend(self._build_env_args(extra_env))
        bwrap_cmd.extend(["--", "/usr/local/bin/python", "-m", "terminaluse.lib.sandbox.entrypoint"])

        # Wrap with timeout command since bubblewrap doesn't have built-in timeout
        # Uses coreutils timeout with SIGKILL after grace period
        cmd = [
            "timeout",
            "--signal=TERM",
            f"--kill-after=5",  # SIGKILL 5 seconds after SIGTERM
            str(config.timeout_seconds),
        ] + bwrap_cmd

        if config.verbose:
            logger.info(f"[SANDBOX VERBOSE] Running: {handler_ref.module}.{handler_ref.function}")
            logger.info(f"[SANDBOX VERBOSE] mounts: {len(mounts) if mounts else 0}")
            logger.info(f"[SANDBOX VERBOSE] Full command: {' '.join(cmd)}")
        else:
            logger.debug(f"Running sandboxed handler: {handler_ref.module}.{handler_ref.function}")
            logger.debug(f"Sandbox command: {' '.join(cmd)}")

        try:
            t_start = time.perf_counter()

            result = subprocess.run(
                cmd,
                input=payload_json,
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds + 10,  # Small buffer over timeout command
            )

            t_end = time.perf_counter()
            duration = t_end - t_start
            logger.info(f"[TIMING] subprocess_total: {duration*1000:.0f}ms for {handler_ref.module}.{handler_ref.function}")

            # Check for timeout (timeout command returns 124 on SIGTERM, 137 on SIGKILL)
            timed_out = result.returncode in (124, 137)

            # Record metrics as OTEL span attributes
            status = "success" if result.returncode == 0 else ("timeout" if timed_out else "error")
            handler_name = f"{handler_ref.module}.{handler_ref.function}"

            # Add attributes to current span for observability
            span = trace.get_current_span()
            if span.is_recording():
                span.set_attribute("sandbox.handler", handler_name)
                span.set_attribute("sandbox.method", method)
                span.set_attribute("sandbox.status", status)
                span.set_attribute("sandbox.duration_seconds", duration)
                span.set_attribute("sandbox.exit_code", result.returncode)
                if result.returncode != 0:
                    error_type = "timeout" if timed_out else "crash"
                    span.set_attribute("sandbox.error_type", error_type)

            # Log detailed info on failure
            if result.returncode != 0:
                if timed_out:
                    logger.warning(f"Handler timed out after {config.timeout_seconds}s: {handler_ref.module}.{handler_ref.function}")
                else:
                    signal_info = ""
                    if result.returncode < 0:
                        import signal

                        try:
                            sig = signal.Signals(-result.returncode)
                            signal_info = f" (signal: {sig.name})"
                        except ValueError:
                            signal_info = f" (signal: {-result.returncode})"

                    logger.error(f"Sandbox process failed: exit_code={result.returncode}{signal_info}")
                    logger.error(f"Sandbox command was: {' '.join(cmd[:10])}...")  # First 10 args
                    if result.stderr:
                        logger.error(f"Sandbox stderr: {result.stderr[:4000]}")
                    if result.stdout:
                        logger.error(f"Sandbox stdout: {result.stdout[:1000]}")
            elif config.verbose:
                # Verbose logging even on success
                logger.info(f"[SANDBOX VERBOSE] Success, exit_code=0")
                if result.stderr:
                    logger.info(f"[SANDBOX VERBOSE] stderr: {result.stderr[:4000]}")
                if result.stdout:
                    logger.info(f"[SANDBOX VERBOSE] stdout: {result.stdout[:1000]}")

            return SandboxResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=timed_out,
            )

        except subprocess.TimeoutExpired as e:
            # This shouldn't happen since timeout command handles it, but just in case
            logger.warning(f"Handler timed out (subprocess): {handler_ref.module}.{handler_ref.function}")
            # e.stdout/stderr can be bytes or str - ensure we return str
            stdout_str = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr_str = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return SandboxResult(
                success=False,
                exit_code=124,  # timeout command exit code
                stdout=stdout_str,
                stderr=stderr_str,
                timed_out=True,
            )

        except Exception as e:
            logger.error(f"Error running sandboxed handler: {e}", exc_info=True)
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                timed_out=False,
            )


# Global runner instance
_runner: SandboxRunner | None = None


def get_sandbox_runner() -> SandboxRunner:
    """Get the global sandbox runner."""
    global _runner
    if _runner is None:
        _runner = SandboxRunner()
    return _runner


def reset_sandbox_runner() -> None:
    """Reset the global sandbox runner (primarily for testing)."""
    global _runner
    _runner = None


async def run_handler_sandboxed(
    method: str,
    handler_ref: HandlerRef,
    params: BaseModel,
    mounts: list[Mount] | None = None,
    extra_env: dict[str, str] | None = None,
    task_id: str | None = None,
) -> SandboxResult:
    """
    Async wrapper for running a handler in a bubblewrap sandbox.

    Uses asyncio.to_thread to avoid blocking the event loop.

    Args:
        method: The JSON-RPC method name (e.g., "event/send")
        handler_ref: Reference to the handler to run
        params: The Pydantic params model to pass to the handler
        mounts: Pre-assembled list of mounts (filesystem, system folders, baked)
        extra_env: Additional environment variables for this invocation
        task_id: Optional task ID for log correlation
    """
    runner = get_sandbox_runner()

    result = await asyncio.to_thread(
        runner.run,
        method,
        handler_ref,
        params,
        mounts,
        extra_env,
    )

    # Send logs to Nucleus (fire-and-forget, don't block on errors)
    await _send_logs_to_nucleus(method, result, task_id)

    return result


async def _send_logs_to_nucleus(
    method: str,
    result: SandboxResult,
    task_id: str | None,
) -> None:
    """
    Send captured stdout/stderr to Nucleus for log ingestion.

    This is a fire-and-forget operation - errors are logged but don't
    affect the handler result.
    """
    if not result.stdout and not result.stderr:
        return

    try:
        from terminaluse.lib.logging import get_log_sender

        log_sender = get_log_sender()
        if log_sender:
            await log_sender.send_logs(
                method=method,
                stdout=result.stdout,
                stderr=result.stderr,
                task_id=task_id,
            )
    except Exception as e:
        logger.warning(f"Failed to send logs to Nucleus: {e}")
