# Copyright (c) Microsoft. All rights reserved.

"""Base abstractions for building agents that plug into Mantisdk."""

from __future__ import annotations

import inspect
import logging
import warnings
import weakref
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar

from mantisdk.types import NamedResources, Rollout, RolloutRawResult, Task

if TYPE_CHECKING:
    from mantisdk.runner import Runner
    from mantisdk.tracer import Tracer
    from mantisdk.trainer import Trainer


logger = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = [
    "LitAgent",
]


def is_v0_1_rollout_api(func: Callable[..., Any]) -> bool:
    """Return `True` when the rollout function uses the deprecated v0.1 signature.

    The helper inspects the callable's signature to detect whether a `rollout_id`
    parameter is present, which indicates the legacy API.

    Args:
        func: Function to analyze.

    Returns:
        `True` if the callable exposes a `rollout_id` parameter.
    """
    return "rollout_id" in inspect.signature(func).parameters


class LitAgent(Generic[T]):
    """Base class for implementing agent rollouts.

    Subclasses override the rollout methods to process tasks while the trainer and
    runner infrastructure manages orchestration, tracing, and persistence.
    """

    def __init__(self, *, trained_agents: Optional[str] = None) -> None:  # FIXME: str | None won't work for cli
        """Initialize the agent instance.

        Args:
            trained_agents: Optional identifier used by legacy tooling to mark trained
                agents.

        !!! warning "Deprecated"
            The `trained_agents` flag is deprecated. Configure `agent_match` in the adapter
            layer instead. See [`TracerTraceToTriplet`][mantisdk.TracerTraceToTriplet]
            for more details.
        """
        if trained_agents is not None:
            warnings.warn(
                "`trained_agents` is deprecated. Configure `agent_match` in adapter instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.trained_agents = trained_agents

        self._trainer_ref: weakref.ReferenceType[Trainer] | None = None
        self._runner_ref: weakref.ReferenceType[Runner[T]] | None = None

    def is_async(self) -> bool:
        """Return `True` when the agent overrides any asynchronous rollout methods.

        Override this method for customized async detection logic.
        """
        return (
            (
                hasattr(self, "training_rollout_async")
                and self.__class__.training_rollout_async is not LitAgent.training_rollout_async  # type: ignore
            )
            or (
                hasattr(self, "validation_rollout_async")
                and self.__class__.validation_rollout_async is not LitAgent.validation_rollout_async  # type: ignore
            )
            or (hasattr(self, "rollout_async") and self.__class__.rollout_async is not LitAgent.rollout_async)  # type: ignore
        )

    def set_trainer(self, trainer: Trainer) -> None:
        """Attach the trainer responsible for orchestration.

        Args:
            trainer: [`Trainer`][mantisdk.Trainer] that manages the agent.
        """
        self._trainer_ref = weakref.ref(trainer)

    def get_trainer(self) -> Trainer:
        """Return the trainer associated with this agent."""
        if self._trainer_ref is None:
            raise ValueError("Trainer has not been set for this agent.")
        trainer = self._trainer_ref()
        if trainer is None:
            raise ValueError("Trainer reference is no longer valid (object has been garbage collected).")
        return trainer

    @property
    def trainer(self) -> Trainer:
        """Return the trainer associated with this agent."""
        return self.get_trainer()

    def get_tracer(self) -> Tracer:
        """Return the tracer configured for this agent."""
        if hasattr(self.runner, "tracer"):
            return self.runner.tracer  # type: ignore
        else:
            return self.trainer.tracer

    @property
    def tracer(self) -> Tracer:
        """Return the tracer configured for this agent."""
        return self.get_tracer()

    def set_runner(self, runner: Runner[T]) -> None:
        """Attach the runner responsible for executing rollouts.

        Args:
            runner: [`Runner`][mantisdk.Runner] coordinating execution.
        """
        self._runner_ref = weakref.ref(runner)

    def get_runner(self) -> Runner[T]:
        """Return the runner responsible for executing rollouts."""
        if self._runner_ref is None:
            raise ValueError("Runner has not been set for this agent.")
        runner = self._runner_ref()
        if runner is None:
            raise ValueError("Runner reference is no longer valid (object has been garbage collected).")
        return runner

    @property
    def runner(self) -> Runner[T]:
        """Return the runner responsible for executing rollouts."""
        return self.get_runner()

    def on_rollout_start(self, task: Task, runner: Runner[T], tracer: Tracer) -> None:
        """Hook invoked immediately before a rollout begins.

        Subclasses can override this method to implement custom logic such as logging,
        metric collection, or resource setup. The default implementation is a no-op.

        Args:
            task: [`Task`][mantisdk.Task] that will be processed.
            runner: [`Runner`][mantisdk.Runner] managing the rollout.
            tracer: [`Tracer`][mantisdk.Tracer] associated with the runner.

        !!! warning "Deprecated"
            Override [`Hook.on_rollout_start`][mantisdk.Hook.on_rollout_start]
            instead of this method when extending agents.
        """

    def on_rollout_end(self, task: Task, rollout: Rollout, runner: Runner[T], tracer: Tracer) -> None:
        """Hook invoked after a rollout completes.

        Subclasses can override this method for cleanup or additional logging. The default
        implementation is a no-op.

        Args:
            task: [`Task`][mantisdk.Task] that was processed.
            rollout: Resulting [`Rollout`][mantisdk.Rollout].
            runner: [`Runner`][mantisdk.Runner] managing the rollout.
            tracer: [`Tracer`][mantisdk.Tracer] associated with the runner.

        !!! warning "Deprecated"
            Override [`Hook.on_rollout_end`][mantisdk.Hook.on_rollout_end]
            instead of this method when extending agents.
        """

    def rollout(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Execute a rollout synchronously.


        If you don't wish to implement both training rollout and validation
        rollout separately, you can just implement `rollout` which will work for both.

        Args:
            task: Task payload provided by the scheduler.
            resources: Mapping of named resources (for example LLMs or prompt templates).
            rollout: Rollout metadata. Avoid mutating this object directly unless a
                subclass needs to override defaults.

        Returns:
            One of the following values:

            * `None` when tracing is handled by the runner.
            * `float` representing the final reward.
            * `List[ReadableSpan]` with OpenTelemetry spans.
            * `List[Span]` with Mantisdk spans.
            * `List[SpanCoreFields]` with Mantisdk spans.
        """
        raise NotImplementedError("Agents must implement the `rollout` method.")

    async def rollout_async(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Execute a rollout asynchronously.

        Args:
            task: Task payload provided by the scheduler.
            resources: Mapping of named resources (for example LLMs or prompt templates).
            rollout: Rollout metadata. Avoid mutating this object directly unless a
                subclass needs to override defaults.

        Returns:
            Same possible return values as
            [`rollout`][mantisdk.LitAgent.rollout].
        """
        raise NotImplementedError("Agents must implement the `rollout_async` method for async operations.")

    def training_rollout(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Process a single training task synchronously.

        By default, this method delegates to
        [`rollout`][mantisdk.LitAgent.rollout].
        """
        return self.rollout(task, resources, rollout)

    def validation_rollout(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Process a single validation task synchronously.

        Override this method when validation should differ from training. The default
        implementation delegates to
        [`training_rollout`][mantisdk.LitAgent.training_rollout].
        """
        return self.rollout(task, resources, rollout)

    async def training_rollout_async(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Process a single training task asynchronously.

        By default, this method delegates to
        [`rollout_async`][mantisdk.LitAgent.rollout_async].
        """
        return await self.rollout_async(task, resources, rollout)

    async def validation_rollout_async(self, task: T, resources: NamedResources, rollout: Rollout) -> RolloutRawResult:
        """Process a single validation task asynchronously.

        Override this method when validation should differ from training. The default
        implementation delegates to
        [`training_rollout_async`][mantisdk.LitAgent.training_rollout_async].
        """
        return await self.rollout_async(task, resources, rollout)
