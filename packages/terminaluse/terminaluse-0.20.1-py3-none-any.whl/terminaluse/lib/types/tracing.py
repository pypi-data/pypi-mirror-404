from __future__ import annotations

from typing import Literal, Annotated

from pydantic import Field

from terminaluse.lib.utils.model_utils import BaseModel


class BaseModelWithTraceParams(BaseModel):
    """
    Base model with trace parameters.

    Attributes:
        trace_id: The trace ID
        parent_span_id: The parent span ID
    """

    trace_id: str | None = None
    parent_span_id: str | None = None


class TerminalUseTracingProcessorConfig(BaseModel):
    type: Literal["terminaluse"] = "terminaluse"


TracingProcessorConfig = Annotated[
    TerminalUseTracingProcessorConfig,
    Field(discriminator="type"),
]
