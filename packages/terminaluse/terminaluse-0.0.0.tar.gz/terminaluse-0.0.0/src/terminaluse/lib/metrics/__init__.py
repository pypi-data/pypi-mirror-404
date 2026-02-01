"""Timing utilities for TerminalUse SDK.

This module provides timing helpers for observability. Metrics are recorded
as OTEL span attributes rather than Prometheus metrics.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator
from dataclasses import dataclass, field

from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)


# =============================================================================
# Timing Helpers
# =============================================================================


@dataclass
class TimingContext:
    """Tracks timing for a single operation with multiple phases."""

    name: str
    start_time: float = field(default_factory=time.perf_counter)
    checkpoints: dict[str, float] = field(default_factory=dict)

    def checkpoint(self, name: str) -> float:
        """Record a checkpoint and return elapsed time since start."""
        now = time.perf_counter()
        elapsed = now - self.start_time
        self.checkpoints[name] = elapsed
        return elapsed

    def elapsed(self) -> float:
        """Return total elapsed time."""
        return time.perf_counter() - self.start_time

    def phase_duration(self, start_checkpoint: str, end_checkpoint: str) -> float:
        """Return duration between two checkpoints."""
        return self.checkpoints.get(end_checkpoint, 0) - self.checkpoints.get(start_checkpoint, 0)

    def log_summary(self) -> None:
        """Log a summary of all timings."""
        total = self.elapsed()
        parts = []
        prev_time = 0.0
        for name, elapsed in self.checkpoints.items():
            duration = elapsed - prev_time
            parts.append(f"{name}={duration*1000:.0f}ms")
            prev_time = elapsed

        logger.info(f"[TIMING] {self.name}: total={total*1000:.0f}ms ({', '.join(parts)})")


@contextmanager
def timed_operation(name: str) -> Generator[TimingContext, None, None]:
    """Context manager for timing operations.

    Example:
        with timed_operation("sandbox_execution") as ctx:
            # do work
            ctx.checkpoint("phase1")
            # more work
            ctx.checkpoint("phase2")
    """
    ctx = TimingContext(name)
    try:
        yield ctx
    finally:
        ctx.log_summary()


__all__ = [
    "TimingContext",
    "timed_operation",
]
