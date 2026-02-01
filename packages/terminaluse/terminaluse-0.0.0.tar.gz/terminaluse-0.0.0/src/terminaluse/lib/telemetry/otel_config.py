"""OpenTelemetry configuration for agent SDK.

Configures OTEL to send telemetry through Nucleus authenticated endpoints,
NOT directly to OTEL Collector. This ensures:
1. Agent identity is verified via x-agent-api-key
2. Resource attributes are enriched server-side with verified identity
3. Rate limiting is enforced per agent
4. Untrusted agent code cannot spoof telemetry for other agents
"""

from __future__ import annotations

import os
from typing import Any, Sequence

from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)

import httpx
from opentelemetry import trace, metrics, context
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricExportResult,
    PeriodicExportingMetricReader,
    MetricsData,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY


def _suppress_instrumentation() -> Any:
    """Get a context with instrumentation suppressed to prevent recursive span creation."""
    ctx = context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True)
    return context.attach(ctx)


def _restore_instrumentation(token: Any) -> None:
    """Restore instrumentation after suppression."""
    if token is not None:
        context.detach(token)


def _attr_value_to_otlp(value: Any) -> dict[str, Any]:
    """Convert a Python attribute value to OTLP JSON format."""
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, bytes):
        return {"bytesValue": value.decode("utf-8", errors="replace")}
    if isinstance(value, (list, tuple)):
        return {"arrayValue": {"values": [_attr_value_to_otlp(v) for v in value]}}
    return {"stringValue": str(value)}


class NucleusSpanExporter(SpanExporter):
    """Span exporter that sends traces to Nucleus /traces endpoint with x-agent-api-key auth."""

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint.rstrip("/") + "/traces"
        self.api_key = api_key
        self._client = httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0))
        logger.debug(f"NucleusSpanExporter initialized: {self.endpoint}")

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to Nucleus."""
        if not spans:
            return SpanExportResult.SUCCESS

        otlp_data = self._spans_to_otlp(list(spans))
        token = _suppress_instrumentation()
        try:
            response = self._client.post(
                self.endpoint,
                json=otlp_data,
                headers={
                    "x-agent-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            logger.debug(f"Exported {len(spans)} spans to Nucleus")
            return SpanExportResult.SUCCESS
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to export spans to Nucleus: HTTP {e.response.status_code}")
            return SpanExportResult.FAILURE
        except Exception as e:
            logger.warning(f"Failed to export spans to Nucleus: {e}")
            return SpanExportResult.FAILURE
        finally:
            _restore_instrumentation(token)

    def shutdown(self) -> None:
        """Shutdown the exporter and close HTTP client."""
        self._client.close()
        logger.debug("NucleusSpanExporter shutdown")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """No-op since this exporter doesn't buffer."""
        return True

    def _spans_to_otlp(self, spans: list[ReadableSpan]) -> dict[str, Any]:
        """Convert SDK spans to OTLP JSON format."""
        resource_data: dict[frozenset[tuple[str, str]], dict[str, Any]] = {}

        for span in spans:
            # Use frozenset of attributes for stable grouping (not memory address)
            if span.resource:
                resource_key = frozenset(
                    (k, str(v)) for k, v in sorted(span.resource.attributes.items())
                )
            else:
                resource_key = frozenset()

            if resource_key not in resource_data:
                resource_attrs = [
                    {"key": k, "value": _attr_value_to_otlp(v)}
                    for k, v in (span.resource.attributes.items() if span.resource else [])
                ]
                resource_data[resource_key] = {
                    "resource": {"attributes": resource_attrs},
                    "scopes": {},
                }

            scope = span.instrumentation_scope
            scope_name = scope.name if scope else "unknown"
            scope_version = scope.version if scope and scope.version else ""
            scope_key = (scope_name, scope_version)

            if scope_key not in resource_data[resource_key]["scopes"]:
                resource_data[resource_key]["scopes"][scope_key] = {
                    "scope": {"name": scope_name, "version": scope_version},
                    "spans": [],
                }

            otlp_span: dict[str, Any] = {
                "traceId": format(span.context.trace_id, "032x"),
                "spanId": format(span.context.span_id, "016x"),
                "name": span.name,
                "kind": span.kind.value if span.kind else 0,
                "startTimeUnixNano": str(span.start_time) if span.start_time else "0",
                "endTimeUnixNano": str(span.end_time) if span.end_time else str(span.start_time or 0),
                "status": {
                    "code": span.status.status_code.value if span.status else 0,
                },
            }

            if span.parent and span.parent.span_id:
                otlp_span["parentSpanId"] = format(span.parent.span_id, "016x")

            if span.attributes:
                otlp_span["attributes"] = [
                    {"key": k, "value": _attr_value_to_otlp(v)}
                    for k, v in span.attributes.items()
                ]

            if span.events:
                otlp_span["events"] = [
                    {
                        "timeUnixNano": str(event.timestamp),
                        "name": event.name,
                        "attributes": [
                            {"key": k, "value": _attr_value_to_otlp(v)}
                            for k, v in (event.attributes or {}).items()
                        ],
                    }
                    for event in span.events
                ]

            resource_data[resource_key]["scopes"][scope_key]["spans"].append(otlp_span)

        return {
            "resourceSpans": [
                {"resource": rd["resource"], "scopeSpans": list(rd["scopes"].values())}
                for rd in resource_data.values()
            ]
        }


class NucleusMetricsExporter(MetricExporter):
    """Metrics exporter that sends to Nucleus /agent-metrics endpoint with x-agent-api-key auth."""

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint.rstrip("/") + "/agent-metrics"
        self.api_key = api_key
        self._client = httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0))
        self._preferred_temporality = {}
        self._preferred_aggregation = {}
        logger.debug(f"NucleusMetricsExporter initialized: {self.endpoint}")

    def export(
        self,
        metrics_data: MetricsData,
        timeout_millis: float = 10000,
        **kwargs: Any,
    ) -> MetricExportResult:
        """Export metrics to Nucleus."""
        if not metrics_data.resource_metrics:
            return MetricExportResult.SUCCESS

        otlp_data = self._metrics_to_otlp(metrics_data)
        token = _suppress_instrumentation()
        try:
            response = self._client.post(
                self.endpoint,
                json=otlp_data,
                headers={
                    "x-agent-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            logger.debug("Exported metrics to Nucleus")
            return MetricExportResult.SUCCESS
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to export metrics to Nucleus: HTTP {e.response.status_code}")
            return MetricExportResult.FAILURE
        except Exception as e:
            logger.warning(f"Failed to export metrics to Nucleus: {e}")
            return MetricExportResult.FAILURE
        finally:
            _restore_instrumentation(token)

    def shutdown(self, timeout_millis: float = 30000, **kwargs: Any) -> None:
        """Shutdown the exporter."""
        self._client.close()
        logger.debug("NucleusMetricsExporter shutdown")

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        """No-op since this exporter doesn't buffer."""
        return True

    def _metrics_to_otlp(self, metrics_data: MetricsData) -> dict[str, Any]:
        """Convert SDK metrics to OTLP JSON format."""
        resource_metrics = []

        for rm in metrics_data.resource_metrics:
            resource_attrs = [
                {"key": k, "value": _attr_value_to_otlp(v)}
                for k, v in (rm.resource.attributes.items() if rm.resource else [])
            ]

            scope_metrics = []
            for sm in rm.scope_metrics:
                metrics_list = []
                for metric in sm.metrics:
                    metric_dict: dict[str, Any] = {
                        "name": metric.name,
                        "description": metric.description or "",
                        "unit": metric.unit or "",
                    }

                    # Handle different metric data types
                    if hasattr(metric, "data") and metric.data:
                        data = metric.data
                        data_points = []

                        for dp in getattr(data, "data_points", []):
                            point: dict[str, Any] = {
                                "startTimeUnixNano": str(getattr(dp, "start_time_unix_nano", 0)),
                                "timeUnixNano": str(getattr(dp, "time_unix_nano", 0)),
                                "attributes": [
                                    {"key": k, "value": _attr_value_to_otlp(v)}
                                    for k, v in (getattr(dp, "attributes", {}) or {}).items()
                                ],
                            }

                            if hasattr(dp, "value"):
                                if isinstance(dp.value, int):
                                    point["asInt"] = str(dp.value)
                                else:
                                    point["asDouble"] = dp.value

                            if hasattr(dp, "bucket_counts"):
                                point["bucketCounts"] = [str(c) for c in dp.bucket_counts]
                            if hasattr(dp, "explicit_bounds"):
                                point["explicitBounds"] = list(dp.explicit_bounds)
                            if hasattr(dp, "sum"):
                                point["sum"] = dp.sum
                            if hasattr(dp, "count"):
                                point["count"] = str(dp.count)

                            data_points.append(point)

                        data_type = type(data).__name__.lower()
                        if "gauge" in data_type:
                            metric_dict["gauge"] = {"dataPoints": data_points}
                        elif "sum" in data_type:
                            metric_dict["sum"] = {
                                "dataPoints": data_points,
                                "aggregationTemporality": getattr(data, "aggregation_temporality", 1),
                                "isMonotonic": getattr(data, "is_monotonic", False),
                            }
                        elif "histogram" in data_type:
                            metric_dict["histogram"] = {
                                "dataPoints": data_points,
                                "aggregationTemporality": getattr(data, "aggregation_temporality", 1),
                            }
                        else:
                            logger.warning(f"Unrecognized metric type '{data_type}' for metric '{metric.name}', data may be lost")

                    metrics_list.append(metric_dict)

                scope_metrics.append({
                    "scope": {
                        "name": sm.scope.name if sm.scope else "unknown",
                        "version": sm.scope.version if sm.scope and sm.scope.version else "",
                    },
                    "metrics": metrics_list,
                })

            resource_metrics.append({
                "resource": {"attributes": resource_attrs},
                "scopeMetrics": scope_metrics,
            })

        return {"resourceMetrics": resource_metrics}


def configure_agent_telemetry(*, auto_instrument: bool = False) -> bool:
    """Configure OpenTelemetry to send telemetry through Nucleus.

    Call this early in agent startup. Telemetry is only enabled if both
    TERMINALUSE_BASE_URL and TERMINALUSE_AGENT_API_KEY are set.

    Args:
        auto_instrument: If True, enables GLOBAL auto-instrumentation for FastAPI
            and httpx. All FastAPI apps and httpx clients in your process will be
            instrumented. Default is False (opt-in).

    What you get by default (auto_instrument=False):
    - TracerProvider configured to export spans to Nucleus
    - MeterProvider configured to export metrics to Nucleus
    - Manual spans via trace.get_tracer() work out of the box

    What auto_instrument=True adds:
    - FastAPI: Server spans for all incoming HTTP requests
    - httpx: Client spans for all outgoing HTTP requests
    - Automatic W3C traceparent/tracestate header propagation

    Environment variables:
    - TERMINALUSE_BASE_URL: Nucleus API URL (required)
    - TERMINALUSE_AGENT_API_KEY: Agent authentication key (required)
    - TERMINALUSE_AGENT_NAME: Service name for traces (optional)
    - TERMINALUSE_AGENT_VERSION: Service version (optional)

    Returns:
        True if telemetry was configured, False if disabled or unavailable

    Example (manual spans only - safe, no global side effects):
        from terminaluse.lib.telemetry import configure_agent_telemetry
        from opentelemetry import trace

        configure_agent_telemetry()

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("my-operation"):
            do_work()

    Example (with auto-instrumentation - global side effects):
        from terminaluse.lib.telemetry import configure_agent_telemetry

        # Call BEFORE creating your FastAPI app
        configure_agent_telemetry(auto_instrument=True)

        app = FastAPI()  # All requests automatically traced
    """
    base_url = os.environ.get("TERMINALUSE_BASE_URL", "")
    api_key = os.environ.get("TERMINALUSE_AGENT_API_KEY", "")

    if not base_url or not api_key:
        logger.debug(
            "Telemetry disabled: TERMINALUSE_BASE_URL or TERMINALUSE_AGENT_API_KEY not set"
        )
        return False

    service_name = os.environ.get("TERMINALUSE_AGENT_NAME", "unknown-agent")
    service_version = os.environ.get("TERMINALUSE_AGENT_VERSION", "unknown")

    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "telemetry.sdk.name": "terminaluse",
        "telemetry.sdk.language": "python",
    })

    span_exporter = NucleusSpanExporter(endpoint=base_url, api_key=api_key)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metrics_exporter = NucleusMetricsExporter(endpoint=base_url, api_key=api_key)
    metrics_reader = PeriodicExportingMetricReader(metrics_exporter, export_interval_millis=60000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metrics_reader])
    metrics.set_meter_provider(meter_provider)

    if auto_instrument:
        _instrument_httpx()
        _instrument_fastapi()
        logger.info(
            f"Telemetry configured with auto-instrumentation: "
            f"traces to {base_url}/traces, metrics to {base_url}/agent-metrics"
        )
    else:
        logger.info(
            f"Telemetry configured (manual spans only): "
            f"traces to {base_url}/traces, metrics to {base_url}/agent-metrics"
        )
    return True


def _instrument_httpx() -> None:
    """Enable httpx auto-instrumentation for trace context propagation."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        instrumentor = HTTPXClientInstrumentor()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()
            logger.debug("HTTPX auto-instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-httpx not installed")
    except Exception as e:
        logger.warning(f"Failed to instrument httpx: {e}")


def _instrument_fastapi() -> None:
    """Enable FastAPI auto-instrumentation for server-side tracing."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        instrumentor = FastAPIInstrumentor()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()
            logger.debug("FastAPI auto-instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-fastapi not installed")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")
