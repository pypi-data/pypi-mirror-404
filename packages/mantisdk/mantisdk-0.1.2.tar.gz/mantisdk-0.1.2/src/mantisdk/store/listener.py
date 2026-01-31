# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from mantisdk.types import Attempt, AttemptedRollout, NamedResources, ResourcesUpdate, Rollout, Span


@runtime_checkable
class StorageListener(Protocol):
    """Protocol for listening to storage events.
    
    Listeners can be attached to a LightningStore to observe state changes
    and perform side effects (logging, tracking, etc.) without modifying
    the core storage logic.
    """

    @property
    def capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of the listener (e.g., {"otlp_traces": True})."""
        ...

    def otlp_traces_endpoint(self) -> Optional[str]:
        """Return OTLP endpoint if supported, else None."""
        ...

    def get_otlp_headers(self) -> Dict[str, str]:
        """Return OTLP headers if supported, else empty dict."""
        ...

    async def on_job_created(self, job_id: str, project_id: Optional[str] = None) -> None:
        """Called when the store/job is initialized."""
        ...

    async def on_rollout_created(self, rollout: Rollout) -> None:
        """Called when a rollout is created (start or enqueue)."""
        ...

    async def on_rollout_updated(self, rollout: Rollout) -> None:
        """Called when a rollout is updated (status change, etc.)."""
        ...

    async def on_attempt_created(self, attempt: Attempt) -> None:
        """Called when an attempt is created."""
        ...

    async def on_attempt_updated(self, attempt: Attempt, rollout_id: str) -> None:
        """Called when an attempt is updated."""
        ...

    async def on_span_created(self, span: Span) -> None:
        """Called when a span is added."""
        ...

    async def on_resource_registered(self, resource: ResourcesUpdate) -> None:
        """Called when a resource snapshot is registered/updated."""
        ...
