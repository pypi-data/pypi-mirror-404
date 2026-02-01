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
import inspect
import json
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, Optional, TypeVar, Union

from opentelemetry import trace as otel_trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

from . import semconv

logger = logging.getLogger(__name__)

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])

# Tracer name for MantisDK spans
TRACER_NAME = "mantisdk.tracing"


# =============================================================================
# Serialization helpers for I/O capture
# =============================================================================


def _safe_serialize(value: Any) -> Any:
    """Recursively serialize a value to JSON-compatible format."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_serialize(v) for k, v in value.items()}
    # Fallback for complex objects (Pydantic models, dataclasses, etc.)
    if hasattr(value, "model_dump"):
        return _safe_serialize(value.model_dump())
    if hasattr(value, "__dict__"):
        return _safe_serialize(vars(value))
    return str(value)


def _serialize_value(value: Any) -> str:
    """Safely serialize a value to a JSON string for span attributes."""
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)):
        return json.dumps(value)
    try:
        return json.dumps(_safe_serialize(value))
    except Exception:
        return str(value)


def _capture_function_input(fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Capture function arguments as a JSON string."""
    try:
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # Filter out 'self' and 'cls' parameters
        input_dict = {
            k: _safe_serialize(v)
            for k, v in bound.arguments.items()
            if k not in ("self", "cls")
        }

        return json.dumps(input_dict) if input_dict else "{}"
    except Exception:
        # Fallback: simple representation
        return json.dumps({
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in kwargs.items()}
        })


def _get_tracer() -> Tracer:
    """Get the MantisDK tracer instance."""
    return otel_trace.get_tracer(TRACER_NAME)


class trace:
    """Create a trace span - works as both a decorator and context manager.

    As a decorator, automatically captures function inputs and outputs::

        @tracing.trace
        def my_function(query: str) -> dict:
            return {"result": query.upper()}

        @tracing.trace(name="custom-name", capture_output=False)
        def another_function(data):
            process(data)

    As a context manager, allows explicit input/output control::

        with tracing.trace("my-workflow", input=query) as span:
            result = do_work()
            span.set_attribute(tracing.semconv.TRACE_OUTPUT, result)

    Args:
        name_or_func: Either the span name (str) or the function to decorate.
        name: Explicit span name (for decorator with custom name).
        input: Input value to capture (context manager mode).
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        capture_input: Auto-capture function input (decorator mode, default: True).
        capture_output: Auto-capture function output (decorator mode, default: True).
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
    """

    def __init__(
        self,
        name_or_func: Optional[Union[str, Callable[..., Any]]] = None,
        *,
        name: Optional[str] = None,
        input: Optional[Any] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None,
        capture_input: bool = True,
        capture_output: bool = True,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ):
        self._name_or_func = name_or_func
        self._explicit_name = name
        self._input = input
        self._kind = kind
        self._attributes = attributes
        self._capture_input = capture_input
        self._capture_output = capture_output
        self._record_exception = record_exception
        self._set_status_on_exception = set_status_on_exception
        self._span: Optional[Span] = None
        self._token: Optional[Any] = None

        # If called as @trace without parentheses, name_or_func is the function
        if callable(name_or_func):
            self._func = name_or_func
            self._span_name = name or name_or_func.__name__
        else:
            self._func = None
            self._span_name = name_or_func or name or "trace"

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle decorator invocation."""
        # If we already have a function, this is the actual call
        if self._func is not None:
            return self._invoke_decorated(self._func, args, kwargs)

        # If first arg is a callable, we're being used as @trace(...) decorator
        if args and callable(args[0]) and not kwargs:
            func = args[0]
            self._func = func
            self._span_name = self._explicit_name or func.__name__

            # Return a wrapper that will be called when the function is invoked
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*a: Any, **kw: Any) -> Any:
                    return await self._invoke_decorated_async(func, a, kw)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*a: Any, **kw: Any) -> Any:
                    return self._invoke_decorated(func, a, kw)
                return sync_wrapper

        raise TypeError("trace() requires a name string or a function")

    def _invoke_decorated(self, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """Invoke a decorated sync function with tracing."""
        tracer = _get_tracer()

        with tracer.start_as_current_span(
            name=self._span_name,
            kind=self._kind,
            attributes=self._attributes,
            record_exception=self._record_exception,
            set_status_on_exception=self._set_status_on_exception,
        ) as span:
            # Capture input
            if self._capture_input:
                input_val = _capture_function_input(func, args, kwargs)
                span.set_attribute(semconv.OBSERVATION_INPUT, input_val)

            result = func(*args, **kwargs)

            # Capture output
            if self._capture_output:
                span.set_attribute(semconv.OBSERVATION_OUTPUT, _serialize_value(result))

            return result

    async def _invoke_decorated_async(self, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """Invoke a decorated async function with tracing."""
        tracer = _get_tracer()

        with tracer.start_as_current_span(
            name=self._span_name,
            kind=self._kind,
            attributes=self._attributes,
            record_exception=self._record_exception,
            set_status_on_exception=self._set_status_on_exception,
        ) as span:
            # Capture input
            if self._capture_input:
                input_val = _capture_function_input(func, args, kwargs)
                span.set_attribute(semconv.OBSERVATION_INPUT, input_val)

            result = await func(*args, **kwargs)

            # Capture output
            if self._capture_output:
                span.set_attribute(semconv.OBSERVATION_OUTPUT, _serialize_value(result))

            return result

    def __enter__(self) -> Span:
        """Context manager entry - start the span."""
        tracer = _get_tracer()
        self._span = tracer.start_span(
            name=self._span_name,
            kind=self._kind,
            attributes=self._attributes,
            record_exception=self._record_exception,
            set_status_on_exception=self._set_status_on_exception,
        )
        # Store the context manager to properly exit later
        self._use_span_cm = otel_trace.use_span(self._span, end_on_exit=False)
        self._use_span_cm.__enter__()

        # Set input if provided
        if self._input is not None:
            self._span.set_attribute(semconv.TRACE_INPUT, _serialize_value(self._input))

        return self._span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - end the span."""
        try:
            if self._span is not None:
                if exc_val is not None and self._record_exception:
                    self._span.record_exception(exc_val)
                if exc_val is not None and self._set_status_on_exception:
                    self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self._span.end()
        finally:
            if hasattr(self, '_use_span_cm') and self._use_span_cm is not None:
                self._use_span_cm.__exit__(exc_type, exc_val, exc_tb)


@contextmanager
def span(
    name: str,
    *,
    input: Optional[Any] = None,
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
        input: Input value to capture (displayed in Insight UI).
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing as tracing

        with tracing.trace("my-workflow"):
            with tracing.span("step.load_data", input=dataset_name) as s:
                data = load_data()
                s.set_attribute(tracing.semconv.OBSERVATION_OUTPUT, str(len(data)))

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
        # Set input if provided
        if input is not None:
            otel_span.set_attribute(semconv.OBSERVATION_INPUT, _serialize_value(input))
        try:
            yield otel_span
        except Exception:
            raise


@contextmanager
def tool(
    name: str,
    *,
    input: Optional[Any] = None,
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
        input: Input value to capture (displayed in Insight UI).
        tool_name: Explicit tool name attribute (defaults to name).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing as tracing

        with tracing.tool("search_database", input=query) as s:
            results = db.execute(query)
            s.set_attribute(tracing.semconv.OBSERVATION_OUTPUT, str(len(results)))
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
        # Set input if provided
        if input is not None:
            otel_span.set_attribute(semconv.OBSERVATION_INPUT, _serialize_value(input))
        try:
            yield otel_span
        except Exception:
            raise


@asynccontextmanager
async def atrace(
    name: str,
    *,
    input: Optional[Any] = None,
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
        input: Input value to capture (displayed in Insight UI).
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing as tracing

        async with tracing.atrace("my-async-workflow", input=query) as span:
            result = await async_operation()
            span.set_attribute(tracing.semconv.TRACE_OUTPUT, result)
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
        # Set input if provided
        if input is not None:
            otel_span.set_attribute(semconv.TRACE_INPUT, _serialize_value(input))
        try:
            yield otel_span
        except Exception:
            raise


@asynccontextmanager
async def aspan(
    name: str,
    *,
    input: Optional[Any] = None,
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
        input: Input value to capture (displayed in Insight UI).
        kind: The span kind (default: INTERNAL).
        attributes: Dictionary of attributes to set on the span.
        record_exception: If True, exceptions are recorded on the span.
        set_status_on_exception: If True, span status is set to ERROR on exception.
        **extra_attributes: Additional attributes as keyword arguments.

    Yields:
        The OpenTelemetry Span object.

    Example::

        import mantisdk.tracing as tracing

        async with tracing.atrace("workflow", input=query):
            async with tracing.aspan("fetch_data") as s:
                data = await fetch()
                s.set_attribute(tracing.semconv.OBSERVATION_OUTPUT, str(len(data)))
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
        # Set input if provided
        if input is not None:
            otel_span.set_attribute(semconv.OBSERVATION_INPUT, _serialize_value(input))
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
    return otel_trace.get_current_span()


# Convenience aliases for decorator-style usage
# These allow: @tracing.trace instead of @tracing.trace_decorator
# The context manager `trace` takes precedence, but when used as decorator
# it works because the context manager returns a span, not a wrapper
