# Copyright (c) Metis. All rights reserved.

"""Standalone tracing module for MantisDK.

This module provides a "one-liner" entry point for instrumenting applications
with OpenTelemetry, compatible with OpenInference and AgentOps ecosystems,
while natively supporting export to Mantis Insight.

Example usage::

    import mantisdk.tracing_claude as tracing

    # Auto-detect Insight from environment variables
    tracing.init()

    # Use context managers for manual spans
    with tracing.trace("my-workflow"):
        with tracing.span("step-1"):
            do_work()

    # Use decorators
    @tracing.trace
    def my_function():
        pass

    # Ensure spans are flushed on shutdown
    tracing.shutdown()

Environment variables for Insight auto-detect:
    - INSIGHT_HOST: The Insight server URL (e.g., "https://insight.withmetis.ai")
    - INSIGHT_PUBLIC_KEY: The public key for authentication (pk-lf-...)
    - INSIGHT_SECRET_KEY: The secret key for authentication (sk-lf-...)
    - INSIGHT_OTLP_ENDPOINT: Optional override for the OTLP endpoint
"""

from .init import init, instrument, shutdown, flush
from .api import trace, span, tool, atrace, aspan

# Re-export exporter factory for explicit configuration
from .exporters.insight import insight as insight_exporter

__all__ = [
    # Initialization
    "init",
    "instrument",
    "shutdown",
    "flush",
    # Context managers (sync)
    "trace",
    "span",
    "tool",
    # Context managers (async)
    "atrace",
    "aspan",
    # Exporter factory
    "insight_exporter",
]
