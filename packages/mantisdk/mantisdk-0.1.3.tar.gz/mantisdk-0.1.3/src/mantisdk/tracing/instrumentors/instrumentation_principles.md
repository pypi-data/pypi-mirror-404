# Instrumentation Principles for MantisDK

Lessons learned from building instrumentors for agent SDKs like `claude-agent-sdk`.

## 1. Know Your Backend's Attribute Expectations

Different tracing backends extract data from different attribute namespaces.

**Example:** Mantis Insight's `OtelIngestionProcessor` only looks for:
```typescript
// packages/shared/src/server/otel/OtelIngestionProcessor.ts
input: attributes["langfuse.observation.input"]
output: attributes["langfuse.observation.output"]
```

**Solution:** Set multiple attribute conventions for maximum compatibility:

```python
# Langfuse (for Mantis Insight visualization)
span.set_attribute("langfuse.observation.input", input_value)
span.set_attribute("langfuse.observation.output", output_value)

# OpenInference (for Phoenix, Arize)
span.set_attribute("input.value", input_value)
span.set_attribute("output.value", output_value)
span.set_attribute("openinference.span.kind", "LLM")

# GenAI (widely supported standard)
span.set_attribute("gen_ai.system", "anthropic")
span.set_attribute("gen_ai.usage.input_tokens", token_count)
```

## 2. Context Propagation is Critical

For child spans to appear correctly nested and for timing to be accurate, you must **activate** the parent context.

**Bad:**
```python
parent_span = tracer.start_span("parent")
# Other instrumentation won't see this as the active parent
child_span = tracer.start_span("child")  # Will be a sibling, not child!
```

**Good:**
```python
parent_span = tracer.start_span("parent")
parent_ctx = trace.set_span_in_context(parent_span)
context_token = attach(parent_ctx)  # Activate!

try:
    # Now other instrumentation sees parent_span as active
    # Their spans will be children automatically
    result = await some_instrumented_function()
finally:
    detach(context_token)  # Clean up
    parent_span.end()
```

**Even Better (explicit context for child spans):**
```python
parent_ctx = trace.set_span_in_context(parent_span)
context_token = attach(parent_ctx)

# Explicitly pass context when creating known children
child_span = tracer.start_span("child", context=parent_ctx)
```

## 3. Root Spans Need Fresh Context

To create separate traces (not nested), use an empty `Context()`:

```python
# Creates a NEW trace (root span)
span = tracer.start_span("operation", context=Context())

# Without context=Context(), this would be a child of any active span
```

**Use case:** In chat applications, each user message should be its own trace, not nested under previous messages.

## 4. Async Generators Require Special Handling

Spans must remain open across async generator boundaries.

**Pattern:**
```python
def _create_instrumented_query(self, original_query):
    async def instrumented_query(client, prompt):
        span = tracer.start_span("conversation")
        span.set_attribute("input", prompt)
        
        # Store span for later use
        setattr(client, "_current_span", span)
        
        try:
            return await original_query(client, prompt)
        except Exception as e:
            span.set_status(StatusCode.ERROR)
            span.end()  # End early on error
            delattr(client, "_current_span")
            raise

def _create_instrumented_receive(self, original_receive):
    async def instrumented_receive(client):
        span = getattr(client, "_current_span", None)
        
        try:
            async for item in original_receive(client):
                # Process items, set output on span
                yield item
                
                if is_final_item(item):
                    span.set_attribute("output", extract_output(item))
                    span.end()
                    delattr(client, "_current_span")
        finally:
            # Cleanup if generator not fully consumed
            if hasattr(client, "_current_span"):
                remaining = getattr(client, "_current_span")
                if remaining.is_recording():
                    remaining.end()
                delattr(client, "_current_span")
```

## 5. Capture All Available Context

Don't just capture the obvious fields - explore the SDK's type definitions for all available data.

**Example:** `claude-agent-sdk` provides:
```python
AssistantMessage.error  # API error type (rate_limit, billing_error, etc.)
AssistantMessage.parent_tool_use_id  # Sub-agent correlation
ThinkingBlock.signature  # Thinking block signature
ResultMessage.structured_output  # Structured response data
SystemMessage.subtype  # System event type (init, mcp_connection, etc.)
```

Capture them all for maximum observability:

```python
if message.error:
    span.set_attribute("claude.api_error", message.error)

if isinstance(message, SystemMessage):
    span.add_event(
        f"system.{message.subtype}",
        attributes={"system.data": json.dumps(message.data)}
    )
```

## 6. Never Truncate Arbitrarily

Truncating attributes like `[:500]` or `[:10000]` breaks observability.

**Bad:**
```python
span.set_attribute("output", long_text[:500])  # Why 500?
```

**Good:**
```python
span.set_attribute("output", long_text)  # Let OTEL handle limits
```

OpenTelemetry SDKs have configurable limits. Arbitrary truncation in instrumentors:
- Loses critical debugging data
- Isn't configurable by users
- Often removes the exact data needed for diagnosis

## 7. Span Kinds: OTel vs. Domain

OpenTelemetry has `SpanKind` (CLIENT, SERVER, INTERNAL), but domain conventions like OpenInference use attributes.

**Set both:**
```python
# OTel SpanKind (for protocol semantics)
span = tracer.start_span("llm_call", kind=SpanKind.CLIENT)

# Domain span kind (for tracing UI semantics)
span.set_attribute("openinference.span.kind", "LLM")
```

Common domain kinds:
- `LLM` - Language model generation
- `TOOL` - Tool/function execution
- `AGENT` - Agent orchestration
- `CHAIN` - Workflow steps

## 8. Timing Accuracy Limitations

Be aware that span timing in streaming contexts reflects **when you receive messages**, not when work actually happened.

```python
# In claude-agent-sdk:
ToolUseBlock arrives → start tool span (time T1)
# ... tool executes in CLI subprocess (actual work happens)
ToolResultBlock arrives → end tool span (time T2)

# T2 - T1 includes:
# - Actual tool execution time
# - Stream buffering delay
# - Network latency
# - Message parsing overhead
```

**Document this limitation:**
```python
# Note: Span timing is based on when we receive ToolUseBlock/ToolResultBlock messages,
# not when the tool actually executes in Claude CLI. This may cause timing inaccuracies.
tool_span = tracer.start_span(f"tool.{block.name}", ...)
```

**Alternative (if SDK provides timing):**
```python
# Some SDKs provide explicit timestamps in result messages
if hasattr(message, 'started_at') and hasattr(message, 'completed_at'):
    tool_span = tracer.start_span(
        name=f"tool.{name}",
        start_time=parse_timestamp(message.started_at),  # Explicit start
    )
    tool_span.end(end_time=parse_timestamp(message.completed_at))  # Explicit end
```

## 9. Centralize Attribute Definitions

Don't hardcode attribute names throughout your instrumentor.

**Bad:**
```python
span.set_attribute("langfuse.observation.input", value)
# ...later in another file...
span.set_attribute("langfuse.observation.input", value)  # Typo risk!
```

**Good:**
```python
# attributes.py
LANGFUSE_OBSERVATION_INPUT = "langfuse.observation.input"
LANGFUSE_OBSERVATION_OUTPUT = "langfuse.observation.output"

# instrumentor.py
from ..attributes import LANGFUSE_OBSERVATION_INPUT
span.set_attribute(LANGFUSE_OBSERVATION_INPUT, value)
```

Benefits:
- Type safety
- Easier refactoring
- Single source of truth
- Documentation via constants

## 10. Preserve Event Sequence

When LLMs interleave text and tool calls, preserve the order:

**Bad (loses sequence):**
```python
# Concatenate all text, list all tools
output = {
    "text": text1 + text2,
    "tool_calls": [tool1, tool2]
}
```

**Good (preserves sequence):**
```python
# Preserve: text → tool_call → text
output_blocks = [
    {"type": "text", "content": text1},
    {"type": "tool_call", "name": "search", "input": {...}, "output": "..."},
    {"type": "text", "content": text2},
]
span.set_attribute("output", json.dumps(output_blocks))
```

This helps understand the agent's reasoning flow: "It said X, then called tool Y, then concluded Z."

## Summary

Building robust instrumentors requires:
1. ✅ Understanding backend attribute expectations
2. ✅ Proper context propagation with `attach()`/`detach()`
3. ✅ Supporting multiple attribute conventions
4. ✅ Careful span lifecycle management in async code
5. ✅ Capturing all available SDK data
6. ✅ Avoiding arbitrary truncation
7. ✅ Being aware of timing limitations in streaming contexts
8. ✅ Centralizing attribute definitions
9. ✅ Preserving event sequences for debugging
