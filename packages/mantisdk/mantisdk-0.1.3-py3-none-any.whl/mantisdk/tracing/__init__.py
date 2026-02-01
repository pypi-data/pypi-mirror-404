# Copyright (c) Metis. All rights reserved.

"""Standalone tracing module for MantisDK.

This module provides a "one-liner" entry point for instrumenting applications
with OpenTelemetry, compatible with OpenInference ecosystem,
while natively supporting export to Mantis Insight.

Example usage::

    import mantisdk.tracing as tracing

    # Auto-detect Insight from environment variables
    tracing.init()

    # Use as a decorator (auto-captures input/output)
    @tracing.trace
    def my_function(query: str) -> dict:
        return {"result": query.upper()}

    # Use as a context manager (explicit input/output)
    with tracing.trace("my-workflow", input=query) as span:
        result = do_work()
        span.set_attribute(tracing.semconv.TRACE_OUTPUT, result)

    # Use semantic conventions for rich metadata
    span.set_attribute(tracing.semconv.USER_ID, "user-123")
    span.set_attribute(tracing.semconv.SESSION_ID, "session-456")

    # Ensure spans are flushed on shutdown
    tracing.shutdown()

Environment variables for Insight auto-detect:
    - INSIGHT_HOST: The Insight server URL (e.g., "https://insight.withmetis.ai")
    - INSIGHT_PUBLIC_KEY: The public key for authentication (pk-lf-...)
    - INSIGHT_SECRET_KEY: The secret key for authentication (sk-lf-...)
    - INSIGHT_OTLP_ENDPOINT: Optional override for the OTLP endpoint
"""

from .init import init, instrument, shutdown, flush
from .api import trace, span, tool, atrace, aspan, get_current_span
from . import semconv

# Re-export exporter factory for explicit configuration
from .exporters.insight import insight as insight_exporter

__all__ = [
    # Initialization
    "init",
    "instrument",
    "shutdown",
    "flush",
    # Context managers / decorators (sync)
    "trace",
    "span",
    "tool",
    # Context managers (async)
    "atrace",
    "aspan",
    # Span utilities
    "get_current_span",
    # Semantic conventions
    "semconv",
    # Exporter factory
    "insight_exporter",
]
