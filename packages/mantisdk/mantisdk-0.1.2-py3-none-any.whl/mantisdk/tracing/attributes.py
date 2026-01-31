# Copyright (c) Metis. All rights reserved.

"""Semantic attributes for MantisDK tracing.

These attributes follow the Mantis Insight OTEL conventions, ensuring
spans are properly processed and displayed in the Insight dashboard.

The attributes are organized by namespace:
- insight.*: Primary namespace for Insight-specific attributes
- gen_ai.*: OpenTelemetry GenAI semantic conventions
- langfuse.*: Compatibility namespace for Langfuse SDK spans
"""

# =============================================================================
# Insight Trace Attributes (Primary Namespace)
# =============================================================================
INSIGHT_TRACE_NAME = "insight.trace.name"
INSIGHT_TRACE_USER_ID = "insight.user.id"
INSIGHT_TRACE_SESSION_ID = "insight.session.id"
INSIGHT_TRACE_TAGS = "insight.trace.tags"
INSIGHT_TRACE_PUBLIC = "insight.trace.public"
INSIGHT_TRACE_METADATA = "insight.trace.metadata"
INSIGHT_TRACE_INPUT = "insight.trace.input"
INSIGHT_TRACE_OUTPUT = "insight.trace.output"

# =============================================================================
# Insight Observation Attributes (Primary Namespace)
# =============================================================================
INSIGHT_OBSERVATION_TYPE = "insight.observation.type"
INSIGHT_OBSERVATION_METADATA = "insight.observation.metadata"
INSIGHT_OBSERVATION_LEVEL = "insight.observation.level"
INSIGHT_OBSERVATION_STATUS_MESSAGE = "insight.observation.status_message"
INSIGHT_OBSERVATION_INPUT = "insight.observation.input"
INSIGHT_OBSERVATION_OUTPUT = "insight.observation.output"
INSIGHT_OBSERVATION_MODEL = "insight.observation.model.name"
INSIGHT_OBSERVATION_MODEL_PARAMETERS = "insight.observation.model.parameters"

# =============================================================================
# Insight General Attributes (Primary Namespace)
# =============================================================================
INSIGHT_ENVIRONMENT = "insight.environment"
INSIGHT_RELEASE = "insight.release"
INSIGHT_VERSION = "insight.version"

# =============================================================================
# Langfuse Trace Attributes (Compatibility)
# =============================================================================
LANGFUSE_TRACE_NAME = "langfuse.trace.name"
LANGFUSE_TRACE_USER_ID = "user.id"
LANGFUSE_TRACE_SESSION_ID = "session.id"
LANGFUSE_TRACE_TAGS = "langfuse.trace.tags"
LANGFUSE_TRACE_PUBLIC = "langfuse.trace.public"
LANGFUSE_TRACE_METADATA = "langfuse.trace.metadata"
LANGFUSE_TRACE_INPUT = "langfuse.trace.input"
LANGFUSE_TRACE_OUTPUT = "langfuse.trace.output"

# =============================================================================
# Langfuse Observation Attributes (Compatibility)
# =============================================================================
LANGFUSE_OBSERVATION_TYPE = "langfuse.observation.type"
LANGFUSE_OBSERVATION_METADATA = "langfuse.observation.metadata"
LANGFUSE_OBSERVATION_LEVEL = "langfuse.observation.level"
LANGFUSE_OBSERVATION_STATUS_MESSAGE = "langfuse.observation.status_message"
LANGFUSE_OBSERVATION_INPUT = "langfuse.observation.input"
LANGFUSE_OBSERVATION_OUTPUT = "langfuse.observation.output"

# =============================================================================
# Langfuse Generation Attributes (Compatibility)
# =============================================================================
LANGFUSE_OBSERVATION_COMPLETION_START_TIME = "langfuse.observation.completion_start_time"
LANGFUSE_OBSERVATION_MODEL = "langfuse.observation.model.name"
LANGFUSE_OBSERVATION_MODEL_PARAMETERS = "langfuse.observation.model.parameters"
LANGFUSE_OBSERVATION_USAGE_DETAILS = "langfuse.observation.usage_details"
LANGFUSE_OBSERVATION_COST_DETAILS = "langfuse.observation.cost_details"
LANGFUSE_OBSERVATION_PROMPT_NAME = "langfuse.observation.prompt.name"
LANGFUSE_OBSERVATION_PROMPT_VERSION = "langfuse.observation.prompt.version"

# =============================================================================
# Langfuse General Attributes (Compatibility)
# =============================================================================
LANGFUSE_ENVIRONMENT = "langfuse.environment"
LANGFUSE_RELEASE = "langfuse.release"
LANGFUSE_VERSION = "langfuse.version"

# =============================================================================
# OpenTelemetry GenAI Semantic Conventions
# https://opentelemetry.io/docs/specs/semconv/gen-ai/
# =============================================================================
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_CONVERSATION_ID = "gen_ai.conversation.id"

# GenAI Input/Output
GEN_AI_INPUT_MESSAGES = "gen_ai.input.messages"
GEN_AI_OUTPUT_MESSAGES = "gen_ai.output.messages"

# GenAI Usage
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_USAGE_COST = "gen_ai.usage.cost"

# GenAI Tool Attributes
GEN_AI_TOOL_NAME = "gen_ai.tool.name"
GEN_AI_TOOL_CALL_ARGUMENTS = "gen_ai.tool.call.arguments"
GEN_AI_TOOL_CALL_RESULT = "gen_ai.tool.call.result"

# =============================================================================
# OpenInference Semantic Conventions
# https://github.com/Arize-ai/openinference
# =============================================================================
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"

# LLM Attributes
LLM_MODEL_NAME = "llm.model_name"
LLM_INVOCATION_PARAMETERS = "llm.invocation_parameters"
LLM_INPUT_MESSAGES = "llm.input_messages"
LLM_OUTPUT_MESSAGES = "llm.output_messages"
LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"

# Input/Output (general)
INPUT_VALUE = "input.value"
OUTPUT_VALUE = "output.value"

# Tool Attributes
TOOL_NAME = "tool.name"
TOOL_DESCRIPTION = "tool.description"
TOOL_PARAMETERS = "tool.parameters"

# =============================================================================
# OpenInference Span Kind Values
# =============================================================================
SPAN_KIND_LLM = "LLM"
SPAN_KIND_TOOL = "TOOL"
SPAN_KIND_AGENT = "AGENT"
SPAN_KIND_CHAIN = "CHAIN"
SPAN_KIND_EMBEDDING = "EMBEDDING"
SPAN_KIND_RETRIEVER = "RETRIEVER"
SPAN_KIND_RERANKER = "RERANKER"
SPAN_KIND_GUARDRAIL = "GUARDRAIL"
SPAN_KIND_EVALUATOR = "EVALUATOR"

# =============================================================================
# OpenInference MIME Types
# =============================================================================
MIME_TYPE_TEXT = "text/plain"
MIME_TYPE_JSON = "application/json"

# =============================================================================
# OpenInference Extended Attributes
# =============================================================================
INPUT_MIME_TYPE = "input.mime_type"
OUTPUT_MIME_TYPE = "output.mime_type"
LLM_SYSTEM = "llm.system"
LLM_PROVIDER = "llm.provider"

# Session/User attributes (OpenInference convention)
SESSION_ID = "session.id"
USER_ID = "user.id"

# Langfuse trace-level session (alias for compatibility)
LANGFUSE_TRACE_SESSION_ID = "session.id"

# =============================================================================
# MantisDK Custom Attributes
# These are additional attributes specific to MantisDK instrumentation
# =============================================================================
MANTIS_LLM_THINKING = "mantis.llm.thinking"
MANTIS_LLM_COST_USD = "mantis.llm.cost_usd"
MANTIS_DURATION_MS = "mantis.duration_ms"
MANTIS_DURATION_API_MS = "mantis.duration_api_ms"
MANTIS_NUM_TURNS = "mantis.num_turns"
MANTIS_TOOL_IS_ERROR = "mantis.tool.is_error"

# =============================================================================
# Claude-Specific Attributes
# These capture Claude Agent SDK-specific data not covered by standard conventions
# =============================================================================
CLAUDE_API_ERROR = "claude.api_error"
CLAUDE_PARENT_TOOL_USE_ID = "claude.parent_tool_use_id"
CLAUDE_STRUCTURED_OUTPUT = "claude.structured_output"
CLAUDE_THINKING_SIGNATURE = "claude.thinking.signature"
CLAUDE_MESSAGE_UUID = "claude.message.uuid"
CLAUDE_SYSTEM_SUBTYPE = "claude.system.subtype"
CLAUDE_SYSTEM_DATA = "claude.system.data"
