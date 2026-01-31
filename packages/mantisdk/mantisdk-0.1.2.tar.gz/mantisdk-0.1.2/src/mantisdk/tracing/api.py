# Copyright (c) Metis. All rights reserved.

"""Context managers and decorators for MantisDK tracing.

This module provides the user-facing API for creating spans:
- trace(): Create a root span (trace)
- span(): Create a child span
- tool(): Create a tool execution span

Both sync and async variants are provided.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, Optional, TypeVar, Union

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])

# Tracer name for MantisDK spans
TRACER_NAME = "mantisdk.tracing"


def _get_tracer() -> trace.Tracer:
    """Get the MantisDK tracer instance."""
    return trace.get_tracer(TRACER_NAME)


@contextmanager
def trace(
    name: str,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes: Any,
) -> Generator[Span, None, None]:
    """Context manager to create a trace (root span).

    This creates a new span that will be the root of a trace tree.
    Child spans created within this context will be linked to this root.

    Args:
        name: The name of the trace/span.
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing_claude as tracing

        tracing.init()

        with tracing.trace("my-workflow", user_id="123") as span:
            span.set_attribute("step", "preprocessing")
            result = do_work()
            span.set_attribute("result_count", len(result))
    """
    tracer = _get_tracer()
    all_attributes = {**(attributes or {}), **extra_attributes}

    with tracer.start_as_current_span(
        name=name,
        kind=kind,
        attributes=all_attributes if all_attributes else None,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as otel_span:
        try:
            yield otel_span
        except Exception as e:
            # Span context manager handles recording; we just re-raise
            raise


@contextmanager
def span(
    name: str,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes: Any,
) -> Generator[Span, None, None]:
    """Context manager to create a child span.

    This creates a span that will be a child of the current active span.
    If no active span exists, it becomes a root span.

    Args:
        name: The name of the span.
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing_claude as tracing

        with tracing.trace("my-workflow"):
            with tracing.span("step.load_data", dataset="training") as s:
                data = load_data()
                s.set_attribute("rows", len(data))

            with tracing.span("step.process"):
                process(data)
    """
    tracer = _get_tracer()
    all_attributes = {**(attributes or {}), **extra_attributes}

    with tracer.start_as_current_span(
        name=name,
        kind=kind,
        attributes=all_attributes if all_attributes else None,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as otel_span:
        try:
            yield otel_span
        except Exception:
            raise


@contextmanager
def tool(
    name: str,
    *,
    tool_name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes: Any,
) -> Generator[Span, None, None]:
    """Context manager to trace a tool execution.

    This creates a span with TOOL kind and semantic attributes for tool calls.
    Useful for tracing function calls, API calls, or other discrete operations.

    Args:
        name: The span name (often the function/tool name).
        tool_name: Explicit tool name attribute (defaults to name).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing_claude as tracing

        with tracing.tool("search_database", query="SELECT *") as s:
            results = db.execute(query)
            s.set_attribute("result_count", len(results))
    """
    tracer = _get_tracer()
    all_attributes = {
        "tool.name": tool_name or name,
        **(attributes or {}),
        **extra_attributes,
    }

    # Use CLIENT kind for tool calls (external service calls)
    with tracer.start_as_current_span(
        name=name,
        kind=SpanKind.CLIENT,
        attributes=all_attributes,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as otel_span:
        try:
            yield otel_span
        except Exception:
            raise


@asynccontextmanager
async def atrace(
    name: str,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes: Any,
) -> AsyncGenerator[Span, None]:
    """Async context manager to create a trace (root span).

    Async variant of trace() for use in async code.

    Args:
        name: The name of the trace/span.
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing_claude as tracing

        async with tracing.atrace("my-async-workflow") as span:
            result = await async_operation()
    """
    tracer = _get_tracer()
    all_attributes = {**(attributes or {}), **extra_attributes}

    with tracer.start_as_current_span(
        name=name,
        kind=kind,
        attributes=all_attributes if all_attributes else None,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as otel_span:
        try:
            yield otel_span
        except Exception:
            raise


@asynccontextmanager
async def aspan(
    name: str,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes: Any,
) -> AsyncGenerator[Span, None]:
    """Async context manager to create a child span.

    Async variant of span() for use in async code.

    Args:
        name: The name of the span.
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing_claude as tracing

        async with tracing.atrace("workflow"):
            async with tracing.aspan("fetch_data") as s:
                data = await fetch()
                s.set_attribute("size", len(data))
    """
    tracer = _get_tracer()
    all_attributes = {**(attributes or {}), **extra_attributes}

    with tracer.start_as_current_span(
        name=name,
        kind=kind,
        attributes=all_attributes if all_attributes else None,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as otel_span:
        try:
            yield otel_span
        except Exception:
            raise


def trace_decorator(
    func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
) -> Union[F, Callable[[F], F]]:
    """Decorator to trace a function execution.

    Can be used with or without parentheses:
        @trace_decorator
        def my_func(): ...

        @trace_decorator(name="custom-name")
        def my_func(): ...

    Works with both sync and async functions.

    Args:
        func: The function to decorate (when used without parentheses).
        name: Custom span name. Defaults to the function name.
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.

    Returns:
        Decorated function.

    Example::

        import mantisdk.tracing_claude as tracing

        @tracing.trace
        def process_data(items):
            return [process(item) for item in items]

        @tracing.trace(name="custom-operation", attributes={"version": "1.0"})
        async def async_operation():
            return await do_something()
    """
    def decorator(fn: F) -> F:
        span_name = name or fn.__name__
        span_attributes = attributes or {}

        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = _get_tracer()
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=kind,
                    attributes=span_attributes if span_attributes else None,
                    record_exception=record_exception,
                    set_status_on_exception=set_status_on_exception,
                ):
                    return await fn(*args, **kwargs)
            return async_wrapper  # type: ignore
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = _get_tracer()
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=kind,
                    attributes=span_attributes if span_attributes else None,
                    record_exception=record_exception,
                    set_status_on_exception=set_status_on_exception,
                ):
                    return fn(*args, **kwargs)
            return sync_wrapper  # type: ignore

    if func is None:
        # Called with parentheses: @trace_decorator(...)
        return decorator
    else:
        # Called without parentheses: @trace_decorator
        return decorator(func)


def tool_decorator(
    func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    tool_name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
) -> Union[F, Callable[[F], F]]:
    """Decorator to trace a tool/function execution.

    Similar to trace_decorator but uses CLIENT span kind and adds tool.name attribute.

    Args:
        func: The function to decorate (when used without parentheses).
        name: Custom span name. Defaults to the function name.
        tool_name: Tool name attribute. Defaults to span name.
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.

    Returns:
        Decorated function.

    Example::

        import mantisdk.tracing_claude as tracing

        @tracing.tool
        def search_database(query: str) -> list:
            return db.execute(query)
    """
    def decorator(fn: F) -> F:
        span_name = name or fn.__name__
        span_attributes = {
            "tool.name": tool_name or span_name,
            **(attributes or {}),
        }

        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = _get_tracer()
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=SpanKind.CLIENT,
                    attributes=span_attributes,
                    record_exception=record_exception,
                    set_status_on_exception=set_status_on_exception,
                ):
                    return await fn(*args, **kwargs)
            return async_wrapper  # type: ignore
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = _get_tracer()
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=SpanKind.CLIENT,
                    attributes=span_attributes,
                    record_exception=record_exception,
                    set_status_on_exception=set_status_on_exception,
                ):
                    return fn(*args, **kwargs)
            return sync_wrapper  # type: ignore

    if func is None:
        return decorator
    else:
        return decorator(func)


def record_exception(
    span: Span,
    exception: BaseException,
    *,
    attributes: Optional[dict[str, Any]] = None,
    escaped: bool = False,
) -> None:
    """Record an exception on a span.

    Helper function for recording exceptions with proper attributes.

    Args:
        span: The span to record the exception on.
        exception: The exception to record.
        attributes: Additional attributes to record with the exception.
        escaped: Whether the exception escaped the span's scope.

    Example::

        import mantisdk.tracing_claude as tracing

        with tracing.span("operation") as s:
            try:
                risky_operation()
            except ValueError as e:
                tracing.record_exception(s, e, attributes={"input": "bad"})
                s.set_status(StatusCode.ERROR, str(e))
                # Handle or re-raise
    """
    span.record_exception(exception, attributes=attributes, escaped=escaped)


def set_span_error(
    span: Span,
    message: str,
    *,
    exception: Optional[BaseException] = None,
) -> None:
    """Set a span's status to ERROR with a description.

    Convenience function for marking a span as failed.

    Args:
        span: The span to mark as error.
        message: Error description.
        exception: Optional exception to record.

    Example::

        import mantisdk.tracing_claude as tracing

        with tracing.span("operation") as s:
            result = do_work()
            if not result.success:
                tracing.set_span_error(s, f"Operation failed: {result.error}")
    """
    span.set_status(Status(StatusCode.ERROR, message))
    if exception is not None:
        span.record_exception(exception)


def set_span_ok(span: Span, message: Optional[str] = None) -> None:
    """Set a span's status to OK.

    Convenience function for marking a span as successful.

    Args:
        span: The span to mark as OK.
        message: Optional success message.
    """
    span.set_status(Status(StatusCode.OK, message))


def get_current_span() -> Span:
    """Get the currently active span.

    Returns:
        The current span, or a non-recording span if none is active.

    Example::

        import mantisdk.tracing_claude as tracing

        def inner_function():
            span = tracing.get_current_span()
            span.set_attribute("inner_data", "value")
    """
    return trace.get_current_span()


# Convenience aliases for decorator-style usage
# These allow: @tracing.trace instead of @tracing.trace_decorator
# The context manager `trace` takes precedence, but when used as decorator
# it works because the context manager returns a span, not a wrapper
