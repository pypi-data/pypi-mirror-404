# Copyright (c) Microsoft. All rights reserved.

from .adapter import (
    MantisdkGEPAAdapter,
    MantisdkDataInst,
    MantisdkTrajectory,
    MantisdkRolloutOutput,
)
from .gepa import GEPA, TEMPLATE_AWARE_REFLECTION_PROMPT
from .tracing import GEPATracingContext

# Re-export the GEPAAdapter from the gepa library for convenience
from mantisdk.algorithm.gepa.lib.core.adapter import GEPAAdapter

# GEPA-specific call type decorators for tagging LLM calls
# Usage: @gepa.judge, @gepa.agent, @gepa.reflection
from mantisdk.types.tracing import call_type_decorator

agent = call_type_decorator("agent-call")
"""Decorator to tag LLM calls as agent calls.

Example:
    >>> @gepa.agent
    >>> def run_agent(client, prompt):
    ...     return client.chat.completions.create(...)  # Tagged as "agent-call"
"""

judge = call_type_decorator("judge-call")
"""Decorator to tag LLM calls as judge/grading calls.

Example:
    >>> @gepa.judge
    >>> def grade_response(client, response, expected):
    ...     return client.chat.completions.parse(...)  # Tagged as "judge-call"
"""

reflection = call_type_decorator("reflection-call")
"""Decorator to tag LLM calls as reflection/optimization calls.

Example:
    >>> @gepa.reflection
    >>> def reflect_on_prompts(client, feedback):
    ...     return client.chat.completions.create(...)  # Tagged as "reflection-call"
"""

__all__ = [
    "GEPA",
    "GEPAAdapter",
    "MantisdkGEPAAdapter",
    "MantisdkDataInst",
    "MantisdkTrajectory",
    "MantisdkRolloutOutput",
    "GEPATracingContext",
    "TEMPLATE_AWARE_REFLECTION_PROMPT",
    # Call type decorators
    "agent",
    "judge",
    "reflection",
]
