# Copyright (c) Microsoft. All rights reserved.

"""Tracing configuration for algorithms.

This module provides a standardized way for algorithms to define their
tracing metadata (environment and tags) that flows through to Mantis/Insight.

It also provides infrastructure for call-type tagging, allowing algorithms
to define decorators that tag LLM calls (e.g., @gepa.judge, @gepa.agent).
"""

import asyncio
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# ============================================================================
# Call Type Context Propagation
# ============================================================================

# Context variable for the current LLM call type (agent, judge, reflection, etc.)
# This is used by instrumentation to tag spans appropriately.
_call_type_context: ContextVar[Optional[str]] = ContextVar("mantis_call_type", default=None)


def get_current_call_type() -> Optional[str]:
    """Get the current LLM call type from context.
    
    Returns:
        The current call type (e.g., "agent-call", "judge-call") or None if not set.
    """
    return _call_type_context.get()


def inject_call_type_header(extra_headers: Optional[dict] = None) -> dict:
    """Inject x-mantis-call-type header from context into extra_headers.
    
    This reads the current call type from context (set by decorators like
    @gepa.agent, @gepa.judge) and adds it to extra_headers for LLM calls.
    The LLM proxy receives this header and tags the trace accordingly.
    
    Args:
        extra_headers: Optional existing headers dict to merge into.
    
    Returns:
        A dict with x-mantis-call-type header if call type is set.
    
    Example:
        >>> @gepa.agent
        >>> def my_agent(client):
        ...     return client.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[...],
        ...         extra_headers=inject_call_type_header()
        ...     )
    """
    if extra_headers is None:
        extra_headers = {}
    
    call_type = get_current_call_type()
    if call_type:
        extra_headers["x-mantis-call-type"] = call_type
    
    return extra_headers


def call_type_decorator(call_type: str) -> Callable[[F], F]:
    """Factory to create call-type tagging decorators.
    
    This is used by algorithms to define their own call-type decorators.
    When a decorated function executes, any LLM calls made within it
    will be tagged with the specified call type.
    
    Args:
        call_type: The call type tag (e.g., "agent-call", "judge-call").
    
    Returns:
        A decorator that sets the call type context for the decorated function.
    
    Example:
        >>> # In algorithm/gepa/__init__.py
        >>> agent = call_type_decorator("agent-call")
        >>> judge = call_type_decorator("judge-call")
        >>> 
        >>> # In user code
        >>> @gepa.judge
        >>> def grade_response(client, response, expected):
        ...     return client.chat.completions.parse(...)  # Tagged as "judge-call"
    """
    def decorator(fn: F) -> F:
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                token = _call_type_context.set(call_type)
                try:
                    return await fn(*args, **kwargs)
                finally:
                    _call_type_context.reset(token)
            return async_wrapper  # type: ignore
        else:
            @wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                token = _call_type_context.set(call_type)
                try:
                    return fn(*args, **kwargs)
                finally:
                    _call_type_context.reset(token)
            return sync_wrapper  # type: ignore
    return decorator


@dataclass
class TracingConfig:
    """Configuration for algorithm-specific tracing metadata.
    
    Each algorithm (GEPA, VERL, etc.) should define its own TracingConfig
    to identify its traces in Mantis. The environment, tags, and session_id are
    propagated through the LLM proxy and stored with traces.
    
    Example:
        >>> config = TracingConfig(
        ...     environment="mantisdk-gepa",
        ...     algorithm_name="gepa"
        ... )
        >>> config.get_tags("train")
        ['gepa', 'train']
    
    Attributes:
        environment: The environment name for traces (e.g., "mantisdk-gepa").
            This appears in Mantis's environment column.
        algorithm_name: The algorithm identifier used as the base tag.
        session_id: Unique session identifier for grouping related traces.
            Auto-generated if not provided.
    """
    
    environment: str
    algorithm_name: str
    session_id: str = field(default_factory=lambda: f"session-{uuid.uuid4().hex[:12]}")
    
    def get_tags(self, trace_type: str) -> List[str]:
        """Generate tags for a specific trace type.
        
        Args:
            trace_type: The type of trace (e.g., "train", "validation", 
                "reflection", "test").
        
        Returns:
            A list of tags: [algorithm_name, trace_type]
        """
        return [self.algorithm_name, trace_type]
    
    def get_detailed_tags(
        self,
        phase: str,
        extra_tags: Optional[List[str]] = None,
    ) -> List[str]:
        """Generate tags with execution context.
        
        Args:
            phase: Execution phase (e.g., "train", "validation", "reflection").
            extra_tags: Optional algorithm-specific tags to append.
        
        Returns:
            A list of tags, e.g.: ["gepa", "train", "custom-tag"]
        """
        tags = [self.algorithm_name, phase]
        
        # Add any algorithm-specific extra tags
        if extra_tags:
            tags.extend(extra_tags)
        
        return tags
    
    def to_metadata(self, trace_type: Optional[str] = None) -> dict:
        """Convert to a metadata dict for rollouts or LLM calls.
        
        Args:
            trace_type: Optional trace type to include in tags.
                If None, only the algorithm_name is included in tags.
        
        Returns:
            Dict with "environment", "tags", and "session_id" keys.
        """
        if trace_type:
            tags = self.get_tags(trace_type)
        else:
            tags = [self.algorithm_name]
        
        return {
            "environment": self.environment,
            "tags": tags,
            "session_id": self.session_id,
        }
    
    def to_detailed_metadata(
        self,
        phase: str,
        extra_tags: Optional[List[str]] = None,
    ) -> dict:
        """Convert to a metadata dict with execution context.
        
        Args:
            phase: Execution phase (e.g., "train", "validation", "reflection").
            extra_tags: Optional algorithm-specific tags to append.
        
        Returns:
            Dict with "environment", "tags", and "session_id" keys.
        """
        return {
            "environment": self.environment,
            "tags": self.get_detailed_tags(phase, extra_tags),
            "session_id": self.session_id,
        }
