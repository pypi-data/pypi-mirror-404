# Copyright (c) Metis. All rights reserved.

"""Instrumentor registry for MantisDK tracing.

This module provides a registry-based system for discovering and managing
OpenTelemetry instrumentors. It supports lazy loading and optional dependencies.
"""

from __future__ import annotations

import importlib.util
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from openinference.instrumentation import TraceConfig

logger = logging.getLogger(__name__)

# Singleton registry instance
_registry: Optional["InstrumentorRegistry"] = None


class BaseInstrumentor(ABC):
    """Base class for instrumentor adapters.

    Each instrumentor adapter wraps a specific instrumentation library
    (OpenInference, AgentOps, etc.) and provides a consistent interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this instrumentor (e.g., 'openai', 'langchain')."""
        pass

    @property
    @abstractmethod
    def package_name(self) -> str:
        """The package name to check for availability."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the instrumentor and its target library are available."""
        pass

    @abstractmethod
    def instrument(self, trace_config: Optional["TraceConfig"] = None) -> None:
        """Activate the instrumentation."""
        pass

    @abstractmethod
    def uninstrument(self) -> None:
        """Deactivate the instrumentation."""
        pass


class OpenInferenceInstrumentor(BaseInstrumentor):
    """Adapter for OpenInference instrumentors.

    OpenInference provides high-quality instrumentors for major LLM libraries
    that emit semantic conventions compatible with observability platforms.
    """

    def __init__(
        self,
        name: str,
        instrumentor_package: str,
        instrumentor_class: str,
        target_package: str,
    ):
        """Initialize the adapter.

        Args:
            name: Unique name for this instrumentor.
            instrumentor_package: Full package path to the instrumentor module.
            instrumentor_class: Class name of the instrumentor.
            target_package: The target library package (e.g., "openai").
        """
        self._name = name
        self._instrumentor_package = instrumentor_package
        self._instrumentor_class = instrumentor_class
        self._target_package = target_package
        self._instance: Optional[object] = None
        self._instrumented = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def package_name(self) -> str:
        return self._instrumentor_package

    def is_available(self) -> bool:
        """Check if both the instrumentor and target library are installed."""
        # Check target library
        if not _is_package_available(self._target_package):
            return False

        # Check instrumentor package
        if not _is_package_available(self._instrumentor_package):
            return False

        return True

    def instrument(self, trace_config: Optional["TraceConfig"] = None) -> None:
        """Activate the OpenInference instrumentation."""
        if self._instrumented:
            logger.debug("Already instrumented: %s", self._name)
            return

        if not self.is_available():
            logger.debug("Cannot instrument %s: dependencies not available", self._name)
            return

        try:
            module = importlib.import_module(self._instrumentor_package)
            instrumentor_class = getattr(module, self._instrumentor_class)
            self._instance = instrumentor_class()

            # OpenInference instrumentors accept trace_config
            if trace_config is not None:
                self._instance.instrument(tracer_provider=None, trace_config=trace_config)
            else:
                self._instance.instrument()

            self._instrumented = True
            logger.debug("Instrumented: %s", self._name)
        except Exception as e:
            logger.warning("Failed to instrument %s: %s", self._name, e)
            raise

    def uninstrument(self) -> None:
        """Deactivate the OpenInference instrumentation."""
        if not self._instrumented or self._instance is None:
            return

        try:
            self._instance.uninstrument()
            self._instrumented = False
            self._instance = None
            logger.debug("Uninstrumented: %s", self._name)
        except Exception as e:
            logger.warning("Failed to uninstrument %s: %s", self._name, e)


class InstrumentorRegistry:
    """Registry for managing instrumentors.

    The registry provides a central place to discover, configure, and manage
    instrumentors from various sources.
    """

    def __init__(self):
        self._instrumentors: Dict[str, BaseInstrumentor] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the default set of instrumentors."""
        # Claude Agent SDK instrumentor (native mantisdk instrumentor)
        from .claude_agent_sdk import ClaudeAgentSDKInstrumentor
        self.register(ClaudeAgentSDKInstrumentor())

        # OpenInference instrumentors (core set)
        openinference_instrumentors = [
            ("openai", "openinference.instrumentation.openai", "OpenAIInstrumentor", "openai"),
            ("anthropic", "openinference.instrumentation.anthropic", "AnthropicInstrumentor", "anthropic"),
            ("langchain", "openinference.instrumentation.langchain", "LangChainInstrumentor", "langchain"),
            ("llama_index", "openinference.instrumentation.llama_index", "LlamaIndexInstrumentor", "llama_index"),
            ("litellm", "openinference.instrumentation.litellm", "LiteLLMInstrumentor", "litellm"),
            # Additional instrumentors
            ("google_adk", "openinference.instrumentation.google_adk", "GoogleADKInstrumentor", "google.adk"),
            ("mistral", "openinference.instrumentation.mistralai", "MistralAIInstrumentor", "mistralai"),
            ("groq", "openinference.instrumentation.groq", "GroqInstrumentor", "groq"),
            ("bedrock", "openinference.instrumentation.bedrock", "BedrockInstrumentor", "boto3"),
            ("vertexai", "openinference.instrumentation.vertexai", "VertexAIInstrumentor", "vertexai"),
            ("dspy", "openinference.instrumentation.dspy", "DSPyInstrumentor", "dspy"),
            ("instructor", "openinference.instrumentation.instructor", "InstructorInstrumentor", "instructor"),
            ("crewai", "openinference.instrumentation.crewai", "CrewAIInstrumentor", "crewai"),
        ]

        for name, package, class_name, target in openinference_instrumentors:
            instrumentor = OpenInferenceInstrumentor(
                name=name,
                instrumentor_package=package,
                instrumentor_class=class_name,
                target_package=target,
            )
            self.register(instrumentor)

    def register(self, instrumentor: BaseInstrumentor) -> None:
        """Register an instrumentor.

        Args:
            instrumentor: The instrumentor to register.
        """
        self._instrumentors[instrumentor.name] = instrumentor
        logger.debug("Registered instrumentor: %s", instrumentor.name)

    def get(self, name: str) -> Optional[BaseInstrumentor]:
        """Get an instrumentor by name.

        Args:
            name: The instrumentor name.

        Returns:
            The instrumentor if found and available, None otherwise.
        """
        instrumentor = self._instrumentors.get(name)
        if instrumentor is None:
            return None

        if not instrumentor.is_available():
            return None

        return instrumentor

    def list_available(self) -> List[str]:
        """List all available instrumentor names.

        Returns:
            List of instrumentor names that are currently available.
        """
        return [
            name for name, instrumentor in self._instrumentors.items()
            if instrumentor.is_available()
        ]

    def list_all(self) -> List[str]:
        """List all registered instrumentor names.

        Returns:
            List of all registered instrumentor names (including unavailable).
        """
        return list(self._instrumentors.keys())

    def instrument_all(
        self,
        names: Optional[List[str]] = None,
        skip: Optional[List[str]] = None,
        trace_config: Optional["TraceConfig"] = None,
    ) -> List[str]:
        """Instrument multiple instrumentors at once.

        Args:
            names: List of instrumentor names to enable. If None, uses the core set.
            skip: List of instrumentor names to skip.
            trace_config: Optional TraceConfig for OpenInference instrumentors.

        Returns:
            List of successfully instrumented names.
        """
        skip_set = set(skip or [])

        if names is None:
            # Core set (includes claude_agent_sdk for automatic tracing)
            target_names = ["claude_agent_sdk", "openai", "anthropic", "langchain", "llama_index", "litellm"]
        else:
            target_names = names

        # Filter out skipped
        target_names = [n for n in target_names if n not in skip_set]

        instrumented = []
        for name in target_names:
            instrumentor = self.get(name)
            if instrumentor is not None:
                try:
                    instrumentor.instrument(trace_config=trace_config)
                    instrumented.append(name)
                except Exception as e:
                    logger.debug("Failed to instrument %s: %s", name, e)

        return instrumented

    def uninstrument_all(self) -> None:
        """Uninstrument all active instrumentors."""
        for instrumentor in self._instrumentors.values():
            try:
                instrumentor.uninstrument()
            except Exception as e:
                logger.debug("Failed to uninstrument %s: %s", instrumentor.name, e)


def get_registry() -> InstrumentorRegistry:
    """Get the global instrumentor registry.

    Returns:
        The singleton InstrumentorRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = InstrumentorRegistry()
    return _registry


def _is_package_available(package_name: str) -> bool:
    """Check if a package is available for import.

    Args:
        package_name: The package name (can be dotted path).

    Returns:
        True if the package is available.
    """
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False
