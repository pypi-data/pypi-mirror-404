# Copyright (c) Metis. All rights reserved.

"""Initialization and lifecycle management for MantisDK tracing.

This module provides the core init(), shutdown(), and flush() functions
for managing the OpenTelemetry TracerProvider lifecycle.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

from .exporters.insight import insight, is_insight_configured

if TYPE_CHECKING:
    from openinference.instrumentation import TraceConfig

logger = logging.getLogger(__name__)

# Module-level state
_initialized = False
_init_lock = threading.Lock()
_provider: Optional[TracerProvider] = None
_processors: List[BatchSpanProcessor] = []


def init(
    *,
    trace_name: Optional[str] = None,
    service_name: Optional[str] = None,
    instrument_default: bool = True,
    instrument_agentops: bool = False,
    exporters: Optional[List[SpanExporter]] = None,
    trace_config: Optional["TraceConfig"] = None,
    force: bool = False,
    integrations: Optional[Dict[str, Any]] = None,
) -> None:
    """Initialize MantisDK standalone tracing.

    This function configures OpenTelemetry with a connection to Mantis Insight
    (if configured via environment variables), and optionally sets up
    auto-instrumentation for common AI libraries.

    Provider Reuse Behavior:
        - If no TracerProvider exists, creates one.
        - If a TracerProvider exists and force=False, reuses it and adds
          processors/exporters (avoiding duplicates).
        - If force=True, replaces the existing TracerProvider.

    Args:
        trace_name: Optional name for the trace (mostly for AgentOps compatibility).
        service_name: Name of the service (mapped to resource attributes).
            Defaults to "mantisdk-tracing".
        instrument_default: Whether to automatically instrument the "core set"
            of libraries (OpenAI, Anthropic, LangChain, LlamaIndex) if installed.
        instrument_agentops: Whether to enable AgentOps helpers (decorators)
            without exporting to AgentOps platform.
        exporters: List of custom OpenTelemetry SpanExporters. If None and
            Insight env vars are configured, auto-creates an Insight exporter.
        trace_config: OpenInference TraceConfig for controlling capture behavior
            (hiding inputs/outputs, etc.). Default captures all.
        force: If True, replaces any existing global TracerProvider. If False
            (default), reuses the existing provider and appends processors.
        integrations: Dictionary for fine-grained control over integrations.
            Example: {"agentops": {"enabled": True, "helpers_only": True}}

    Example::

        import mantisdk.tracing_claude as tracing

        # Minimal: auto-detect Insight from env vars, auto-instrument
        tracing.init()

        # Explicit configuration
        tracing.init(
            service_name="my-agent",
            exporters=[tracing.insight_exporter(
                host="https://insight.withmetis.ai",
                public_key="pk-lf-...",
                secret_key="sk-lf-...",
            )],
            instrument_default=True,
        )

        # Ensure cleanup on shutdown
        import atexit
        atexit.register(tracing.shutdown)
    """
    global _initialized, _provider, _processors

    with _init_lock:
        # Check existing provider
        current_provider = trace.get_tracer_provider()
        has_sdk_provider = isinstance(current_provider, TracerProvider)

        if _initialized and not force:
            logger.debug("MantisDK tracing already initialized. Use force=True to reinitialize.")
            return

        if has_sdk_provider and not force:
            # Reuse existing provider
            logger.info("Reusing existing TracerProvider")
            _provider = current_provider
        else:
            # Create new provider
            resource_attrs = {
                SERVICE_NAME: service_name or "mantisdk-tracing",
            }
            if trace_name:
                resource_attrs["trace.name"] = trace_name

            resource = Resource.create(resource_attrs)
            _provider = TracerProvider(resource=resource)

            # Set as global provider
            trace.set_tracer_provider(_provider)
            logger.info("Created new TracerProvider with service_name=%s", service_name or "mantisdk-tracing")

        # Configure exporters
        configured_exporters = exporters or []

        # Auto-detect Insight if no exporters provided
        if not configured_exporters and is_insight_configured():
            try:
                insight_exporter = insight()
                configured_exporters.append(insight_exporter)
                logger.info("Auto-configured Insight exporter from environment variables")
            except ValueError as e:
                logger.warning("Could not auto-configure Insight exporter: %s", e)

        # Add processors for each exporter (idempotent)
        for exporter in configured_exporters:
            _add_processor_idempotent(_provider, exporter)

        # Run instrumentation
        if instrument_default:
            instrument()

        if instrument_agentops:
            _setup_agentops_helpers(integrations)

        _initialized = True
        logger.info("MantisDK tracing initialized successfully")


def instrument(
    names: Optional[List[str]] = None,
    skip: Optional[List[str]] = None,
) -> None:
    """Manually enable specific instrumentations.

    This function looks up instrumentors by name from the registry and
    activates them. If no names are provided and init() was called with
    instrument_default=True, this enables the "core set".

    Core Set (enabled by default):
        - openai
        - anthropic
        - langchain
        - llama_index
        - litellm

    Additional Available:
        - google_adk
        - mistral
        - groq
        - bedrock

    Args:
        names: List of instrumentor names to enable. If None and called from
            init() with instrument_default=True, enables the core set.
        skip: List of instrumentor names to explicitly skip.

    Example::

        import mantisdk.tracing_claude as tracing

        # Enable only specific instrumentors
        tracing.init(instrument_default=False)
        tracing.instrument(names=["openai", "anthropic"])

        # Enable all except langchain
        tracing.instrument(skip=["langchain"])
    """
    from .instrumentors.registry import get_registry

    registry = get_registry()
    skip_set = set(skip or [])

    # Determine which instrumentors to enable
    if names is None:
        # Default core set (includes claude_agent_sdk for automatic tracing)
        target_names = ["claude_agent_sdk", "openai", "anthropic", "langchain", "llama_index", "litellm"]
    else:
        target_names = names

    # Filter out skipped instrumentors
    target_names = [name for name in target_names if name not in skip_set]

    # Activate each instrumentor
    for name in target_names:
        instrumentor = registry.get(name)
        if instrumentor is not None:
            try:
                instrumentor.instrument()
                logger.debug("Instrumented: %s", name)
            except Exception as e:
                logger.debug("Could not instrument %s: %s", name, e)
        else:
            logger.debug("Instrumentor not available (not installed?): %s", name)


def shutdown(timeout_millis: int = 30000) -> None:
    """Force flush all pending spans and shutdown the tracer provider.

    This function should be called before process exit to ensure all spans
    are exported. It is safe to call multiple times.

    Args:
        timeout_millis: Maximum time to wait for flush completion in milliseconds.

    Example::

        import mantisdk.tracing_claude as tracing
        import atexit

        tracing.init()
        atexit.register(tracing.shutdown)

        # ... run application ...
    """
    global _initialized, _provider, _processors

    with _init_lock:
        if not _initialized or _provider is None:
            logger.debug("Tracing not initialized, nothing to shutdown")
            return

        try:
            # Shutdown the provider (which flushes and shuts down processors)
            _provider.shutdown()
            logger.info("TracerProvider shutdown complete")
        except Exception as e:
            logger.warning("Error during TracerProvider shutdown: %s", e)

        _processors.clear()
        _initialized = False
        _provider = None


def flush(timeout_millis: int = 30000) -> bool:
    """Force flush all pending spans without shutting down.

    This is useful for ensuring spans are exported at specific points
    (e.g., after completing a batch of work) without ending the tracing session.

    Args:
        timeout_millis: Maximum time to wait for flush completion in milliseconds.

    Returns:
        True if flush completed successfully, False otherwise.

    Example::

        import mantisdk.tracing_claude as tracing

        tracing.init()

        # Process batch
        for item in batch:
            process(item)

        # Ensure all spans from this batch are exported
        tracing.flush()
    """
    global _provider

    with _init_lock:
        if _provider is None:
            logger.debug("No provider to flush")
            return True

        try:
            success = _provider.force_flush(timeout_millis=timeout_millis)
            if success:
                logger.debug("Flush completed successfully")
            else:
                logger.warning("Flush timed out after %d ms", timeout_millis)
            return success
        except Exception as e:
            logger.warning("Error during flush: %s", e)
            return False


def _add_processor_idempotent(provider: TracerProvider, exporter: SpanExporter) -> None:
    """Add a BatchSpanProcessor for the exporter, avoiding duplicates.

    Checks if a processor for the same exporter type/endpoint already exists
    to prevent duplicate exports.
    """
    global _processors

    # Check for existing processor with same exporter type
    exporter_id = _get_exporter_id(exporter)
    for existing in _processors:
        if _get_exporter_id(existing.span_exporter) == exporter_id:
            logger.debug("Processor already exists for exporter: %s", exporter_id)
            return

    # Create and add new processor
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    _processors.append(processor)
    logger.debug("Added BatchSpanProcessor for: %s", exporter_id)


def _get_exporter_id(exporter: SpanExporter) -> str:
    """Generate a unique identifier for an exporter instance.

    Uses class name + endpoint (if available) to identify exporters.
    """
    class_name = exporter.__class__.__name__

    # Try to get endpoint for OTLP exporters
    endpoint = getattr(exporter, "_endpoint", None)
    if endpoint:
        return f"{class_name}:{endpoint}"

    return class_name


def _setup_agentops_helpers(integrations: Optional[Dict[str, Any]] = None) -> None:
    """Enable AgentOps helpers (decorators) without AgentOps export.

    This sets up AgentOps instrumentation in "helpers only" mode,
    where spans are created but exported through MantisDK's exporter
    rather than AgentOps's backend.
    """
    config = (integrations or {}).get("agentops", {})
    if not config.get("enabled", True):
        return

    try:
        import agentops
        # AgentOps init with no API key = helpers only mode
        # The spans will go through our TracerProvider
        logger.debug("AgentOps helpers mode enabled")
    except ImportError:
        logger.debug("AgentOps not installed, skipping helpers setup")


def get_tracer(name: str = "mantisdk.tracing") -> trace.Tracer:
    """Get a tracer instance for creating spans.

    This is primarily for internal use. Users should prefer the
    trace() and span() context managers.

    Args:
        name: The tracer name (instrumentation scope).

    Returns:
        OpenTelemetry Tracer instance.
    """
    return trace.get_tracer(name)
