# Copyright (c) Metis. All rights reserved.

"""Instrumentor for claude-agent-sdk.

This module provides automatic instrumentation for the Claude Agent SDK,
capturing conversation turns, tool calls, and response metadata.

Spans are annotated with semantic attributes following Mantis Insight conventions,
ensuring proper processing and display in the Insight dashboard.
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, AsyncIterator, Optional, TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode
from opentelemetry.context import attach, detach, Context

from .registry import BaseInstrumentor, _is_package_available
from ..attributes import (
    # Langfuse observation attributes (MUST use these for OtelIngestionProcessor to extract I/O)
    LANGFUSE_OBSERVATION_INPUT,
    LANGFUSE_OBSERVATION_OUTPUT,
    LANGFUSE_OBSERVATION_MODEL,
    # OpenTelemetry GenAI attributes (widely supported)
    GEN_AI_SYSTEM,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_RESPONSE_MODEL,
    GEN_AI_USAGE_INPUT_TOKENS,
    GEN_AI_USAGE_OUTPUT_TOKENS,
    GEN_AI_USAGE_COST,
    GEN_AI_OPERATION_NAME,
    GEN_AI_TOOL_NAME,
    GEN_AI_TOOL_CALL_ARGUMENTS,
    GEN_AI_TOOL_CALL_RESULT,
    # OpenInference attributes
    OPENINFERENCE_SPAN_KIND,
    SPAN_KIND_LLM,
    SPAN_KIND_TOOL,
    INPUT_VALUE,
    INPUT_MIME_TYPE,
    OUTPUT_VALUE,
    OUTPUT_MIME_TYPE,
    MIME_TYPE_TEXT,
    MIME_TYPE_JSON,
    LLM_MODEL_NAME,
    LLM_SYSTEM,
    LLM_PROVIDER,
    LLM_TOKEN_COUNT_PROMPT,
    LLM_TOKEN_COUNT_COMPLETION,
    LLM_TOKEN_COUNT_TOTAL,
    TOOL_NAME,
    SESSION_ID,
    # MantisDK custom attributes
    MANTIS_LLM_THINKING,
    MANTIS_LLM_COST_USD,
    MANTIS_DURATION_MS,
    MANTIS_DURATION_API_MS,
    MANTIS_NUM_TURNS,
    MANTIS_TOOL_IS_ERROR,
    # Claude-specific attributes
    CLAUDE_API_ERROR,
    CLAUDE_PARENT_TOOL_USE_ID,
    CLAUDE_STRUCTURED_OUTPUT,
    CLAUDE_THINKING_SIGNATURE,
    CLAUDE_MESSAGE_UUID,
    CLAUDE_SYSTEM_SUBTYPE,
    CLAUDE_SYSTEM_DATA,
)

if TYPE_CHECKING:
    from openinference.instrumentation import TraceConfig

logger = logging.getLogger(__name__)

# Tracer name for claude-agent-sdk spans
TRACER_NAME = "mantisdk.instrumentation.claude_agent_sdk"

# Attribute to store span on client instance
_CLIENT_SPAN_ATTR = "_mantisdk_conversation_span"


class ClaudeAgentSDKInstrumentor(BaseInstrumentor):
    """Instrumentor for claude-agent-sdk.

    This instrumentor wraps the ClaudeSDKClient to automatically create
    OpenTelemetry spans for:
    - Conversation turns (query calls)
    - Tool executions
    - Response processing

    Example::

        import mantisdk.tracing as tracing

        # Auto-instruments claude-agent-sdk if installed
        tracing.init()

        # Now all ClaudeSDKClient usage is traced
        from claude_agent_sdk import ClaudeSDKClient
        client = ClaudeSDKClient()
        # ...
    """

    def __init__(self):
        self._instrumented = False
        self._original_query: Optional[Any] = None
        self._original_receive_messages: Optional[Any] = None

    @property
    def name(self) -> str:
        return "claude_agent_sdk"

    @property
    def package_name(self) -> str:
        return "claude_agent_sdk"

    def is_available(self) -> bool:
        """Check if claude-agent-sdk is installed."""
        return _is_package_available("claude_agent_sdk")

    def instrument(self, trace_config: Optional["TraceConfig"] = None) -> None:
        """Activate instrumentation for claude-agent-sdk.

        This wraps ClaudeSDKClient.query() and receive_messages() to
        automatically create spans for conversation turns.
        """
        if self._instrumented:
            logger.debug("claude_agent_sdk already instrumented")
            return

        if not self.is_available():
            logger.debug("claude_agent_sdk not available, skipping instrumentation")
            return

        try:
            from claude_agent_sdk import ClaudeSDKClient

            # Store original methods
            self._original_query = ClaudeSDKClient.query
            self._original_receive_messages = ClaudeSDKClient.receive_messages

            # Create instrumented versions
            instrumented_query = self._create_instrumented_query(self._original_query)
            instrumented_receive_messages = self._create_instrumented_receive_messages(
                self._original_receive_messages
            )

            # Patch the methods
            ClaudeSDKClient.query = instrumented_query
            ClaudeSDKClient.receive_messages = instrumented_receive_messages

            self._instrumented = True
            logger.info("Instrumented claude_agent_sdk")

        except Exception as e:
            logger.warning("Failed to instrument claude_agent_sdk: %s", e)
            raise

    def uninstrument(self) -> None:
        """Deactivate instrumentation for claude-agent-sdk."""
        if not self._instrumented:
            return

        try:
            from claude_agent_sdk import ClaudeSDKClient

            # Restore original methods
            if self._original_query is not None:
                ClaudeSDKClient.query = self._original_query
            if self._original_receive_messages is not None:
                ClaudeSDKClient.receive_messages = self._original_receive_messages

            self._instrumented = False
            self._original_query = None
            self._original_receive_messages = None
            logger.info("Uninstrumented claude_agent_sdk")

        except Exception as e:
            logger.warning("Failed to uninstrument claude_agent_sdk: %s", e)

    def _create_instrumented_query(self, original_query):
        """Create an instrumented version of ClaudeSDKClient.query().
        
        This creates a span and stores it on the client instance so that
        receive_messages() can add output attributes to it later.
        """

        @functools.wraps(original_query)
        async def instrumented_query(
            client_self,
            prompt: str | Any,
            session_id: str = "default",
        ) -> None:
            tracer = trace.get_tracer(TRACER_NAME)

            # Get model from client options
            model = getattr(client_self.options, "model", None) or "claude"

            # Create span as a NEW TRACE (fresh context = each turn is its own trace)
            span = tracer.start_span(
                "llm.conversation_turn",
                kind=SpanKind.CLIENT,
                context=Context(),  # Empty context creates a new root trace
            )

            # Record input using multiple conventions for compatibility
            input_value = prompt if isinstance(prompt, str) else str(prompt)
            
            # Langfuse attributes (REQUIRED for OtelIngestionProcessor to extract I/O)
            span.set_attribute(LANGFUSE_OBSERVATION_INPUT, input_value)
            span.set_attribute(LANGFUSE_OBSERVATION_MODEL, model)
            
            # OpenInference attributes
            span.set_attribute(OPENINFERENCE_SPAN_KIND, SPAN_KIND_LLM)
            span.set_attribute(INPUT_VALUE, input_value)
            span.set_attribute(INPUT_MIME_TYPE, MIME_TYPE_TEXT)
            span.set_attribute(LLM_MODEL_NAME, model)
            span.set_attribute(LLM_SYSTEM, "anthropic")
            span.set_attribute(LLM_PROVIDER, "anthropic")
            
            # GenAI attributes
            span.set_attribute(GEN_AI_REQUEST_MODEL, model)
            span.set_attribute(GEN_AI_SYSTEM, "anthropic")
            span.set_attribute(GEN_AI_OPERATION_NAME, "chat")

            # Session ID (both conventions)
            span.set_attribute(SESSION_ID, session_id)

            # Store span on client instance for receive_messages to use
            setattr(client_self, _CLIENT_SPAN_ATTR, span)

            try:
                # Call original method
                result = await original_query(client_self, prompt, session_id)
                return result
            except Exception as e:
                # On error, end the span here
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.end()
                # Clear the stored span
                if hasattr(client_self, _CLIENT_SPAN_ATTR):
                    delattr(client_self, _CLIENT_SPAN_ATTR)
                raise

        return instrumented_query

    def _create_instrumented_receive_messages(self, original_receive_messages):
        """Create an instrumented version of ClaudeSDKClient.receive_messages().
        
        This uses the span created by query() to record output attributes,
        then ends the span when ResultMessage is received.
        
        The output is structured as a sequence of blocks to preserve the order:
        text → tool_call → text (if that's how the response came)
        
        Tool calls appear as child spans under the conversation turn span.
        """

        @functools.wraps(original_receive_messages)
        async def instrumented_receive_messages(client_self) -> AsyncIterator[Any]:
            tracer = trace.get_tracer(TRACER_NAME)

            # Import message types
            from claude_agent_sdk import (
                AssistantMessage,
                ResultMessage,
                SystemMessage,
                TextBlock,
                ThinkingBlock,
                ToolUseBlock,
                ToolResultBlock,
                UserMessage,
            )

            # Get the span created by query()
            conversation_span: Optional[Span] = getattr(client_self, _CLIENT_SPAN_ATTR, None)
            
            # Create and ACTIVATE context for proper parent-child span relationships
            # This ensures other instrumented code (MCP, Snowflake, etc.) creates child spans
            parent_ctx = None
            context_token = None
            if conversation_span:
                parent_ctx = trace.set_span_in_context(conversation_span)
                context_token = attach(parent_ctx)  # Activate so other instrumentation sees it

            # Track state for this conversation turn
            output_blocks = []  # Sequence of blocks: text, tool_call, text...
            collected_thinking = []
            thinking_signatures = []  # ThinkingBlock signatures
            tool_spans = {}  # Map tool_use_id to span
            current_text_buffer = []
            system_events = []  # SystemMessage events

            try:
                async for message in original_receive_messages(client_self):
                    if isinstance(message, AssistantMessage):
                        model = getattr(message, "model", None)
                        if conversation_span and conversation_span.is_recording():
                            # Update model from response (GenAI convention)
                            if model:
                                conversation_span.set_attribute(GEN_AI_RESPONSE_MODEL, model)
                                conversation_span.set_attribute(LANGFUSE_OBSERVATION_MODEL, model)
                                conversation_span.set_attribute(LLM_MODEL_NAME, model)
                            
                            # Capture API error if present
                            if message.error:
                                conversation_span.set_attribute(CLAUDE_API_ERROR, message.error)
                            
                            # Capture parent_tool_use_id for sub-agent tracking
                            if message.parent_tool_use_id:
                                conversation_span.set_attribute(CLAUDE_PARENT_TOOL_USE_ID, message.parent_tool_use_id)

                        for block in message.content:
                            if isinstance(block, TextBlock):
                                current_text_buffer.append(block.text)

                            elif isinstance(block, ThinkingBlock):
                                collected_thinking.append(block.thinking)
                                # Capture thinking signature if present
                                if hasattr(block, 'signature') and block.signature:
                                    thinking_signatures.append(block.signature)

                            elif isinstance(block, ToolUseBlock):
                                # Flush any buffered text before tool call
                                if current_text_buffer:
                                    output_blocks.append({
                                        "type": "text",
                                        "content": "\n".join(current_text_buffer)
                                    })
                                    current_text_buffer = []
                                
                                # Add tool call block (will be updated with result)
                                output_blocks.append({
                                    "type": "tool_call",
                                    "name": block.name,
                                    "id": block.id,
                                    "input": block.input,
                                    "output": None
                                })
                                
                                # Create a child span for this tool call
                                # Note: Span timing is based on when we receive ToolUseBlock/ToolResultBlock messages,
                                # not when the tool actually executes in Claude CLI. This may cause timing inaccuracies.
                                tool_span = tracer.start_span(
                                    f"tool.{block.name}",
                                    kind=SpanKind.INTERNAL,
                                    context=parent_ctx,
                                )
                                
                                # OpenInference attributes
                                tool_span.set_attribute(OPENINFERENCE_SPAN_KIND, SPAN_KIND_TOOL)
                                tool_span.set_attribute(TOOL_NAME, block.name)
                                
                                # GenAI attributes
                                tool_span.set_attribute(GEN_AI_TOOL_NAME, block.name)
                                tool_span.set_attribute(GEN_AI_OPERATION_NAME, "tool_call")
                                
                                try:
                                    input_json = json.dumps(block.input)
                                    # GenAI
                                    tool_span.set_attribute(GEN_AI_TOOL_CALL_ARGUMENTS, input_json)
                                    # Langfuse
                                    tool_span.set_attribute(LANGFUSE_OBSERVATION_INPUT, input_json)
                                    # OpenInference
                                    tool_span.set_attribute(INPUT_VALUE, input_json)
                                    tool_span.set_attribute(INPUT_MIME_TYPE, MIME_TYPE_JSON)
                                except (TypeError, ValueError):
                                    input_str = str(block.input)
                                    tool_span.set_attribute(GEN_AI_TOOL_CALL_ARGUMENTS, input_str)
                                    tool_span.set_attribute(LANGFUSE_OBSERVATION_INPUT, input_str)
                                    tool_span.set_attribute(INPUT_VALUE, input_str)
                                    tool_span.set_attribute(INPUT_MIME_TYPE, MIME_TYPE_TEXT)

                                tool_spans[block.id] = tool_span

                    elif isinstance(message, UserMessage):
                        # Capture UserMessage uuid and parent_tool_use_id if present
                        if conversation_span and conversation_span.is_recording():
                            if hasattr(message, 'uuid') and message.uuid:
                                conversation_span.set_attribute(CLAUDE_MESSAGE_UUID, message.uuid)
                            if hasattr(message, 'parent_tool_use_id') and message.parent_tool_use_id:
                                conversation_span.set_attribute(CLAUDE_PARENT_TOOL_USE_ID, message.parent_tool_use_id)
                        
                        # Check for tool results
                        if isinstance(message.content, list):
                            for block in message.content:
                                if isinstance(block, ToolResultBlock):
                                    tool_span = tool_spans.get(block.tool_use_id)
                                    content_str = str(block.content) if block.content else ""
                                    is_error = getattr(block, "is_error", False) or False
                                    
                                    # Update the tool_call block in output_blocks
                                    for ob in output_blocks:
                                        if ob.get("type") == "tool_call" and ob.get("id") == block.tool_use_id:
                                            ob["output"] = content_str
                                            ob["is_error"] = is_error
                                            break
                                    
                                    if tool_span:
                                        # GenAI
                                        tool_span.set_attribute(GEN_AI_TOOL_CALL_RESULT, content_str)
                                        # Langfuse
                                        tool_span.set_attribute(LANGFUSE_OBSERVATION_OUTPUT, content_str)
                                        # OpenInference
                                        tool_span.set_attribute(OUTPUT_VALUE, content_str)
                                        # Determine output mime type based on content
                                        if content_str.strip().startswith('{') or content_str.strip().startswith('['):
                                            tool_span.set_attribute(OUTPUT_MIME_TYPE, MIME_TYPE_JSON)
                                        else:
                                            tool_span.set_attribute(OUTPUT_MIME_TYPE, MIME_TYPE_TEXT)
                                        # MantisDK
                                        tool_span.set_attribute(MANTIS_TOOL_IS_ERROR, is_error)

                                        if is_error:
                                            tool_span.set_status(Status(StatusCode.ERROR, content_str))
                                        else:
                                            tool_span.set_status(Status(StatusCode.OK))

                                        tool_span.end()
                                        del tool_spans[block.tool_use_id]

                    elif isinstance(message, SystemMessage):
                        # Handle SystemMessage - contains system events with subtype and data
                        system_events.append({
                            "subtype": message.subtype,
                            "data": message.data
                        })
                        
                        # Add as event on the conversation span
                        if conversation_span and conversation_span.is_recording():
                            event_attrs = {CLAUDE_SYSTEM_SUBTYPE: message.subtype}
                            if message.data:
                                try:
                                    event_attrs[CLAUDE_SYSTEM_DATA] = json.dumps(message.data)
                                except (TypeError, ValueError):
                                    event_attrs[CLAUDE_SYSTEM_DATA] = str(message.data)
                            conversation_span.add_event(
                                f"system.{message.subtype}",
                                attributes=event_attrs
                            )

                    elif isinstance(message, ResultMessage):
                        # Flush any remaining text buffer
                        if current_text_buffer:
                            output_blocks.append({
                                "type": "text",
                                "content": "\n".join(current_text_buffer)
                            })
                            current_text_buffer = []
                        
                        # Record final metrics on the conversation span
                        if conversation_span and conversation_span.is_recording():
                            # Output attributes (multiple conventions)
                            if output_blocks:
                                text_only = all(b["type"] == "text" for b in output_blocks)
                                if text_only:
                                    full_response = "\n".join(b["content"] for b in output_blocks)
                                    # Langfuse
                                    conversation_span.set_attribute(LANGFUSE_OBSERVATION_OUTPUT, full_response)
                                    # OpenInference
                                    conversation_span.set_attribute(OUTPUT_VALUE, full_response)
                                    conversation_span.set_attribute(OUTPUT_MIME_TYPE, MIME_TYPE_TEXT)
                                else:
                                    output_json = json.dumps(output_blocks, indent=2)
                                    # Langfuse
                                    conversation_span.set_attribute(LANGFUSE_OBSERVATION_OUTPUT, output_json)
                                    # OpenInference
                                    conversation_span.set_attribute(OUTPUT_VALUE, output_json)
                                    conversation_span.set_attribute(OUTPUT_MIME_TYPE, MIME_TYPE_JSON)

                            # Thinking content
                            if collected_thinking:
                                conversation_span.set_attribute(
                                    MANTIS_LLM_THINKING, "\n".join(collected_thinking)
                                )
                            
                            # Thinking signatures (Claude-specific)
                            if thinking_signatures:
                                conversation_span.set_attribute(
                                    CLAUDE_THINKING_SIGNATURE, "\n".join(thinking_signatures)
                                )

                            # Structured output (Claude-specific)
                            if hasattr(message, 'structured_output') and message.structured_output is not None:
                                try:
                                    conversation_span.set_attribute(
                                        CLAUDE_STRUCTURED_OUTPUT, json.dumps(message.structured_output)
                                    )
                                except (TypeError, ValueError):
                                    conversation_span.set_attribute(
                                        CLAUDE_STRUCTURED_OUTPUT, str(message.structured_output)
                                    )

                            # Cost (GenAI and MantisDK)
                            if message.total_cost_usd is not None:
                                conversation_span.set_attribute(GEN_AI_USAGE_COST, message.total_cost_usd)
                                conversation_span.set_attribute(MANTIS_LLM_COST_USD, message.total_cost_usd)

                            # Token usage (GenAI and OpenInference)
                            if message.usage:
                                usage = message.usage
                                input_tokens = usage.get("input_tokens")
                                output_tokens = usage.get("output_tokens")
                                
                                if input_tokens is not None:
                                    # GenAI
                                    conversation_span.set_attribute(GEN_AI_USAGE_INPUT_TOKENS, input_tokens)
                                    # OpenInference
                                    conversation_span.set_attribute(LLM_TOKEN_COUNT_PROMPT, input_tokens)
                                
                                if output_tokens is not None:
                                    # GenAI
                                    conversation_span.set_attribute(GEN_AI_USAGE_OUTPUT_TOKENS, output_tokens)
                                    # OpenInference
                                    conversation_span.set_attribute(LLM_TOKEN_COUNT_COMPLETION, output_tokens)
                                
                                if input_tokens is not None and output_tokens is not None:
                                    conversation_span.set_attribute(
                                        LLM_TOKEN_COUNT_TOTAL, input_tokens + output_tokens
                                    )

                            # Duration (MantisDK)
                            conversation_span.set_attribute(MANTIS_DURATION_MS, message.duration_ms)
                            conversation_span.set_attribute(MANTIS_DURATION_API_MS, message.duration_api_ms)

                            # Turns (MantisDK)
                            conversation_span.set_attribute(MANTIS_NUM_TURNS, message.num_turns)

                            # Session ID (update with final session_id)
                            conversation_span.set_attribute(SESSION_ID, message.session_id)

                            # Error status
                            if message.is_error:
                                conversation_span.set_status(
                                    Status(StatusCode.ERROR, message.result or "Unknown error")
                                )
                            else:
                                conversation_span.set_status(Status(StatusCode.OK))

                            # End the conversation span
                            conversation_span.end()

                        # Clear the stored span
                        if hasattr(client_self, _CLIENT_SPAN_ATTR):
                            delattr(client_self, _CLIENT_SPAN_ATTR)

                    # Yield the original message unchanged
                    yield message

            finally:
                # Detach context first so cleanup doesn't create orphan spans
                if context_token is not None:
                    detach(context_token)
                
                # Clean up any unclosed tool spans
                for tool_id, tool_span in tool_spans.items():
                    tool_span.set_status(Status(StatusCode.ERROR, "Tool span not properly closed"))
                    tool_span.end()

                # Ensure conversation span is ended if not already
                if hasattr(client_self, _CLIENT_SPAN_ATTR):
                    remaining_span = getattr(client_self, _CLIENT_SPAN_ATTR)
                    if remaining_span and remaining_span.is_recording():
                        if current_text_buffer:
                            output_blocks.append({
                                "type": "text",
                                "content": "\n".join(current_text_buffer)
                            })
                        if output_blocks:
                            text_only = all(b["type"] == "text" for b in output_blocks)
                            if text_only:
                                remaining_span.set_attribute(
                                    LANGFUSE_OBSERVATION_OUTPUT, 
                                    "\n".join(b["content"] for b in output_blocks)
                                )
                            else:
                                remaining_span.set_attribute(
                                    LANGFUSE_OBSERVATION_OUTPUT, 
                                    json.dumps(output_blocks, indent=2)
                                )
                        remaining_span.set_status(Status(StatusCode.OK))
                        remaining_span.end()
                    delattr(client_self, _CLIENT_SPAN_ATTR)

        return instrumented_receive_messages
