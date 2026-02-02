import os
import logging
import contextvars

# Lazy imports for faster CLI startup
# ddtrace and json_log_formatter are only needed for non-local environments

ctx_var_request_id = contextvars.ContextVar[str]("request_id")

# Cached datadog configuration check
_datadog_configured: bool | None = None


def _is_datadog_configured() -> bool:
    """Lazy check for datadog configuration."""
    global _datadog_configured
    if _datadog_configured is None:
        _datadog_configured = bool(os.environ.get("DD_AGENT_HOST"))
    return _datadog_configured


def _get_json_formatter_class():
    """Lazy import of JSON formatter with ddtrace support."""
    import ddtrace
    import json_log_formatter

    class CustomJSONFormatter(json_log_formatter.JSONFormatter):
        def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:  # type: ignore[override]
            extra = super().json_record(message, extra, record)
            extra["level"] = record.levelname
            extra["name"] = record.name
            extra["lineno"] = record.lineno
            extra["pathname"] = record.pathname
            extra["request_id"] = ctx_var_request_id.get(None)
            if _is_datadog_configured():
                extra["dd.trace_id"] = ddtrace.tracer.get_log_correlation_context().get("dd.trace_id", None) or getattr(  # type: ignore[attr-defined]
                    record, "dd.trace_id", 0
                )
                extra["dd.span_id"] = ddtrace.tracer.get_log_correlation_context().get("dd.span_id", None) or getattr(  # type: ignore[attr-defined]
                    record, "dd.span_id", 0
                )
            # add the env, service, and version configured for the tracer
            # If tracing is not set up, then this should pull values from DD_ENV, DD_SERVICE, and DD_VERSION.
            service_override = ddtrace.config.service or os.getenv("DD_SERVICE")
            if service_override:
                extra["dd.service"] = service_override

            env_override = ddtrace.config.env or os.getenv("DD_ENV")
            if env_override:
                extra["dd.env"] = env_override

            version_override = ddtrace.config.version or os.getenv("DD_VERSION")
            if version_override:
                extra["dd.version"] = version_override

            return extra

    return CustomJSONFormatter


def make_logger(name: str) -> logging.Logger:
    """
    Creates a logger object with a RichHandler to print colored text.
    :param name: The name of the module to create the logger for.
    :return: A logger object.
    """
    # Create a console object to print colored text
    logger = logging.getLogger(name)
    # Default to WARNING for CLI usage (local development)
    # Default to INFO for deployed agents (when TERMINALUSE_BASE_URL is set, indicating a deployed agent)
    # Can be overridden with TERMINALUSE_LOG_LEVEL env var
    is_deployed_agent = bool(os.getenv("TERMINALUSE_BASE_URL"))
    default_level = "INFO" if is_deployed_agent else "WARNING"
    log_level = os.getenv("TERMINALUSE_LOG_LEVEL", default_level).upper()
    logger.setLevel(getattr(logging, log_level, logging.WARNING))

    environment = os.getenv("ENVIRONMENT")
    if environment == "local":
        # Lazy import of rich - only needed for local development
        from rich.console import Console
        from rich.logging import RichHandler

        console = Console()
        # Add the RichHandler to the logger to print colored text
        handler = RichHandler(
            console=console,
            show_level=False,
            show_path=False,
            show_time=False,
        )
        logger.addHandler(handler)
        return logger

    stream_handler = logging.StreamHandler()
    if _is_datadog_configured():
        CustomJSONFormatter = _get_json_formatter_class()
        stream_handler.setFormatter(CustomJSONFormatter())
    else:
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s")
        )

    logger.addHandler(stream_handler)
    # Create a logger object with the name of the current module
    return logger
