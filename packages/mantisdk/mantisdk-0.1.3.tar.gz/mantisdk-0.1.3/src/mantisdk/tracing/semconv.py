# Copyright (c) Metis. All rights reserved.

"""Mantisdk Semantic Conventions for Tracing.

These attributes align with Insight's primary namespace for optimal
display in the Insight UI. Insight also supports OpenInference,
Langfuse, and other SDK conventions via its attribute alias system.

See: insight/packages/shared/src/server/otel/attributeAliases.ts

Usage::

    import mantisdk.tracing as tracing

    with tracing.trace("my-task", input=query) as span:
        span.set_attribute(tracing.semconv.USER_ID, "user-123")
        span.set_attribute(tracing.semconv.SESSION_ID, "session-456")
        result = do_work()
        span.set_attribute(tracing.semconv.TRACE_OUTPUT, result)
"""

# =============================================================================
# Trace-level attributes (for root spans)
# =============================================================================
TRACE_NAME = "insight.trace.name"
TRACE_INPUT = "insight.trace.input"
TRACE_OUTPUT = "insight.trace.output"
TRACE_METADATA = "insight.trace.metadata"
TRACE_TAGS = "insight.trace.tags"
TRACE_PUBLIC = "insight.trace.public"

# =============================================================================
# User & Session
# =============================================================================
USER_ID = "insight.user.id"
SESSION_ID = "insight.session.id"

# =============================================================================
# Environment & Version
# =============================================================================
ENVIRONMENT = "insight.environment"
RELEASE = "insight.release"
VERSION = "insight.version"

# =============================================================================
# Observation-level attributes (for child spans)
# =============================================================================
OBSERVATION_TYPE = "insight.observation.type"
OBSERVATION_INPUT = "insight.observation.input"
OBSERVATION_OUTPUT = "insight.observation.output"
OBSERVATION_METADATA = "insight.observation.metadata"
OBSERVATION_LEVEL = "insight.observation.level"
OBSERVATION_STATUS_MESSAGE = "insight.observation.status_message"

# =============================================================================
# Model & Generation attributes
# =============================================================================
MODEL_NAME = "insight.observation.model.name"
MODEL_PARAMETERS = "insight.observation.model.parameters"


# =============================================================================
# Observation types (values for OBSERVATION_TYPE)
# =============================================================================
class ObservationType:
    """Valid values for the OBSERVATION_TYPE attribute."""

    SPAN = "span"
    GENERATION = "generation"
    EVENT = "event"


# =============================================================================
# Observation levels (values for OBSERVATION_LEVEL)
# =============================================================================
class ObservationLevel:
    """Valid values for the OBSERVATION_LEVEL attribute."""

    DEBUG = "DEBUG"
    DEFAULT = "DEFAULT"
    WARNING = "WARNING"
    ERROR = "ERROR"
