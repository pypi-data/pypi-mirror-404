# Copyright (c) Microsoft. All rights reserved.

"""LiteLLM instrumentations.

Patches LiteLLM's OpenTelemetry integration to add Mantisdk-specific attributes
to spans, including session_id, tags, environment, and call_type from context.

The call_type is read from a ContextVar that is set by algorithm-specific
decorators (e.g., @gepa.judge, @gepa.agent).

[Related documentation](https://docs.litellm.ai/docs/observability/agentops_integration).
"""

import json
from typing import Any, Optional

from litellm.integrations.opentelemetry import OpenTelemetry

from mantisdk.types.tracing import get_current_call_type

__all__ = [
    "instrument_litellm",
    "uninstrument_litellm",
]

original_set_attributes = OpenTelemetry.set_attributes  # type: ignore


def patched_set_attributes(self: Any, span: Any, kwargs: Any, response_obj: Optional[Any]):
    """Enhanced set_attributes that adds Mantisdk tracing metadata to spans.
    
    Extracts session_id, tags, and environment from kwargs["metadata"] and sets
    them as OTEL span attributes for visibility in Insight/Langfuse.
    
    Also reads the current call_type from context (set by decorators like
    @gepa.judge) and adds it as a span attribute.
    """
    original_set_attributes(self, span, kwargs, response_obj)
    
    # Add token IDs if available
    if response_obj is not None and response_obj.get("prompt_token_ids"):
        span.set_attribute("prompt_token_ids", list(response_obj.get("prompt_token_ids")))
    if response_obj is not None and response_obj.get("response_token_ids"):
        span.set_attribute("response_token_ids", list(response_obj.get("response_token_ids")[0]))
    
    # Read call_type from context (set by @gepa.judge, @gepa.agent, etc.)
    call_type = get_current_call_type()
    if call_type:
        span.set_attribute("mantis.call_type", call_type)
    
    # Extract Mantisdk tracing metadata from kwargs
    metadata = kwargs.get("metadata", {}) if kwargs else {}
    if not metadata:
        return
    
    # Set session_id as span attribute (standard Langfuse/Insight attribute)
    session_id = metadata.get("session_id")
    if session_id:
        span.set_attribute("session.id", session_id)
    
    # Set tags as span attribute (JSON array for Langfuse compatibility)
    tags = metadata.get("tags")
    if tags and isinstance(tags, list):
        # Langfuse expects tags as a JSON array string or individual attributes
        span.set_attribute("tags", json.dumps(tags))
        # Also set individual tag attributes for filtering
        for i, tag in enumerate(tags):
            span.set_attribute(f"tag.{i}", str(tag))
    
    # Set environment as span attribute
    environment = metadata.get("environment")
    if environment:
        span.set_attribute("environment", environment)


def instrument_litellm():
    """Instrument litellm to capture token IDs."""
    OpenTelemetry.set_attributes = patched_set_attributes


def uninstrument_litellm():
    """Uninstrument litellm to stop capturing token IDs."""
    OpenTelemetry.set_attributes = original_set_attributes
