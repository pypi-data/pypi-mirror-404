"""Telemetry configuration for the TerminalUse SDK.

Telemetry (traces, metrics, log correlation) is automatically configured
when you create an AgentServer. No manual setup required.

Control via environment variables:
- TERMINALUSE_TELEMETRY=false: Disable telemetry entirely
- TERMINALUSE_AUTO_INSTRUMENT=false: Disable auto-instrumentation (manual spans only)

Prerequisites (set by platform when deploying agents):
- TERMINALUSE_BASE_URL: Nucleus API URL
- TERMINALUSE_AGENT_API_KEY: Agent authentication key

What's automatic with auto-instrumentation (default):
- HTTP server spans for all incoming FastAPI requests
- HTTP client spans for all outgoing httpx requests
- W3C trace context propagation
- Log correlation (logs include trace_id/span_id)

Manual spans (works with or without auto-instrumentation):
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("my_operation"):
        do_work()

Advanced: If you need to configure telemetry before AgentServer
(rare - usually not needed):
    from terminaluse.lib.telemetry import configure_agent_telemetry
    configure_agent_telemetry(auto_instrument=True)
"""

from terminaluse.lib.telemetry.otel_config import configure_agent_telemetry

__all__ = ["configure_agent_telemetry"]
