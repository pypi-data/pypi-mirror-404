# Copyright (c) Microsoft. All rights reserved.

"""InsightTracker - A StorageListener that streams state to Insight.

This module provides two ways to use Insight tracking:

1. **InsightTracker** (recommended): A StorageListener that can be attached to any store.
   ```python
   from mantisdk.store import InMemoryLightningStore, InsightTracker

   tracker = InsightTracker(
       api_key="pk-lf-abc123",
       secret_key="sk-lf-xyz789",
       insight_url="https://insight.withmetis.ai",
       project_id="proj-123",
   )
   store = InMemoryLightningStore(listeners=[tracker])
   ```

2. **InsightLightningStore** (convenience): Pre-configured InMemoryLightningStore with InsightTracker.
   ```python
   from mantisdk.store import InsightLightningStore

   store = InsightLightningStore(
       api_key="pk-lf-abc123",
       secret_key="sk-lf-xyz789",
       insight_url="https://insight.withmetis.ai",
       project_id="proj-123",
   )
   ```

Both approaches provide:
- Non-blocking event streaming via background thread
- Fault-tolerant operation (network issues don't crash the agent)
- Batched HTTP requests to minimize overhead
- Full resource content tracking
- OTLP trace export support
- Automatic reward-to-score conversion (rewards sent as Insight scores)
"""

from __future__ import annotations

import atexit
import base64
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from mantisdk.emitter.reward import get_rewards_from_span, is_reward_span
from mantisdk.types import (
    Attempt,
    ResourcesUpdate,
    Rollout,
    Span,
)

from .listener import StorageListener

logger = logging.getLogger(__name__)


@dataclass
class InsightEvent:
    """An event to be sent to the Insight API."""

    id: str
    type: str
    timestamp: str  # ISO 8601 datetime string
    data: Dict[str, Any]


class InsightTracker:
    """A StorageListener that streams storage events to Insight.

    This tracker implements the StorageListener protocol and can be attached
    to any LightningStore to enable Insight tracking.

    Features:
    - Non-blocking: Never slow down the agent execution
    - Fault-tolerant: Network issues don't crash the agent
    - Batched: Reduce HTTP overhead by buffering events
    - Full content: Sends complete resource content for experiment tracking

    Args:
        api_key: Insight public API key for authentication.
        secret_key: Insight secret key for authentication.
        insight_url: Insight server URL (e.g., "http://localhost:3000").
        project_id: Project ID to associate events with.
        flush_interval: Seconds between automatic flushes (default: 1.0).
        max_buffer_size: Maximum events before forcing a flush (default: 1000).
        request_timeout: HTTP request timeout in seconds (default: 10.0).
        max_retries: Maximum retry attempts for failed requests (default: 3).
    """

    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        insight_url: str,
        project_id: str,
        flush_interval: float = 1.0,
        max_buffer_size: int = 1000,
        request_timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        # Store configuration
        self._api_key = api_key
        self._secret_key = secret_key
        self._insight_url = insight_url.rstrip("/")
        self._project_id = project_id
        self._flush_interval = flush_interval
        self._max_buffer_size = max_buffer_size
        self._request_timeout = request_timeout
        self._max_retries = max_retries

        # Generate a unique job ID for this tracker instance
        self._job_id = f"job-{uuid.uuid4().hex[:12]}"

        # Track if job has been completed to prevent double-complete
        self._completed = False

        # Event buffer (thread-safe queue)
        self._event_buffer: queue.Queue[InsightEvent] = queue.Queue()

        # Background sender thread control
        self._stop_event = threading.Event()
        self._sender_thread: Optional[threading.Thread] = None

        # Start the background sender thread
        self._start_sender_thread()

        # Emit job.created event immediately
        self._emit_job_created()

        # Register cleanup on exit
        atexit.register(self._cleanup)

        logger.info(
            f"InsightTracker initialized - streaming to {self._insight_url} "
            f"(project={self._project_id}, job={self._job_id})"
        )

    # ─────────────────────────────────────────────────────────────
    # StorageListener Protocol Implementation
    # ─────────────────────────────────────────────────────────────

    @property
    def capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of the listener."""
        return {
            "otlp_traces": True,  # Enable OTLP trace export to Insight
        }

    @property
    def job_id(self) -> str:
        """Return the job ID for this tracker instance."""
        return self._job_id

    def otlp_traces_endpoint(self) -> Optional[str]:
        """Return the OTLP/HTTP traces endpoint."""
        endpoint = f"{self._insight_url}/api/public/otel/v1/traces"
        logger.debug(f"OTLP traces endpoint: {endpoint}")
        return endpoint

    def get_otlp_headers(self) -> Dict[str, str]:
        """Return the authentication headers for OTLP export.

        Insight's OTLP endpoint uses Basic Auth with format: public_key:secret_key
        """
        credentials = f"{self._api_key}:{self._secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
        }

    async def on_job_created(self, job_id: str, project_id: Optional[str] = None) -> None:
        """Called when a job is created. (Usually handled internally)"""
        pass  # We emit job.created in __init__

    async def on_rollout_created(self, rollout: Rollout) -> None:
        """Called when a rollout is created."""
        self._emit(
            "rollout.created",
            {
                "id": rollout.rollout_id,
                "input": rollout.input,
                "status": rollout.status,
                "resource_id": rollout.resources_id,
                "mode": rollout.mode,
                "start_time": rollout.start_time,
                "config": {
                    "max_attempts": rollout.config.max_attempts,
                    "retry_condition": rollout.config.retry_condition,
                    "timeout_seconds": rollout.config.timeout_seconds,
                    "unresponsive_seconds": rollout.config.unresponsive_seconds,
                },
                "metadata": rollout.metadata,
            },
        )

    async def on_rollout_updated(self, rollout: Rollout) -> None:
        """Called when a rollout is updated."""
        data: Dict[str, Any] = {
            "id": rollout.rollout_id,
            "status": rollout.status,
        }
        if rollout.end_time is not None:
            data["end_time"] = rollout.end_time
        self._emit("rollout.status_changed", data)

    async def on_attempt_created(self, attempt: Attempt) -> None:
        """Called when an attempt is created."""
        self._emit(
            "attempt.created",
            {
                "id": attempt.attempt_id,
                "rollout_id": attempt.rollout_id,
                "sequence_id": attempt.sequence_id,
                "status": attempt.status,
                "start_time": attempt.start_time,
                "worker_id": attempt.worker_id,
            },
        )

    async def on_attempt_updated(self, attempt: Attempt, rollout_id: str) -> None:
        """Called when an attempt is updated."""
        data: Dict[str, Any] = {
            "id": attempt.attempt_id,
            "rollout_id": rollout_id,
            "status": attempt.status,
        }
        if attempt.end_time is not None:
            data["end_time"] = attempt.end_time
        self._emit("attempt.status_changed", data)

    async def on_span_created(self, span: Span) -> None:
        """Called when a span is added.
        
        If the span is a reward span, also sends the reward as an Insight score.
        """
        # Emit span event to the event buffer
        self._emit(
            "span.emitted",
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "attempt_id": span.attempt_id,
                "rollout_id": span.rollout_id,
                "sequence_id": span.sequence_id,
                "name": span.name,
                "status": {
                    "status_code": span.status.status_code,
                    "description": span.status.description,
                },
                "attributes": span.attributes,
                "start_time": span.start_time,
                "end_time": span.end_time,
            },
        )

        # Check if this is a reward span and send as Insight score
        if is_reward_span(span):
            rewards = get_rewards_from_span(span)
            for reward in rewards:
                self._send_score(
                    name=reward.name,
                    value=reward.value,
                    trace_id=span.trace_id,
                    observation_id=span.span_id,
                    rollout_id=span.rollout_id,
                    attempt_id=span.attempt_id,
                )

    async def on_resource_registered(self, resource: ResourcesUpdate) -> None:
        """Called when a resource is registered/updated.
        
        Sends FULL resource content for complete experiment tracking.
        """
        # Serialize resources to JSON-compatible dicts
        # Resources are Pydantic models (PromptTemplate, LLM, etc.) which need model_dump()
        serialized_resources: Dict[str, Any] = {}
        for name, res in resource.resources.items():
            if hasattr(res, "model_dump"):
                serialized_resources[name] = res.model_dump()
            elif hasattr(res, "dict"):
                # Fallback for older Pydantic v1 models
                serialized_resources[name] = res.dict()
            else:
                # Already a dict or primitive
                serialized_resources[name] = res
        
        self._emit(
            "resource.registered",
            {
                "id": resource.resources_id,
                "version": resource.version,
                "create_time": resource.create_time,
                "update_time": resource.update_time,
                "resources": serialized_resources,
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Event Emission Helpers
    # ─────────────────────────────────────────────────────────────

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to the buffer for later sending."""
        # Format: 2026-01-17T19:51:40.123Z (Zod datetime expects 'Z' suffix for UTC)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        event = InsightEvent(
            id=f"evt-{uuid.uuid4().hex[:8]}",
            type=event_type,
            timestamp=timestamp,
            data=data,
        )
        try:
            self._event_buffer.put_nowait(event)
        except queue.Full:
            logger.warning(f"Event buffer full, dropping event: {event_type}")
            return

        # Force flush if buffer is at capacity
        if self._event_buffer.qsize() >= self._max_buffer_size:
            self._trigger_flush()

    def _emit_job_created(self) -> None:
        """Emit the job.created event when the tracker is initialized."""
        self._emit(
            "job.created",
            {
                "project_id": self._project_id,
                "type": "agent",
            },
        )
        # Immediately flush to ensure job is created before other events
        self._flush_events()

    def _send_score(
        self,
        name: str,
        value: float,
        trace_id: str,
        observation_id: Optional[str] = None,
        rollout_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> None:
        """Send a score to Insight's /api/public/scores endpoint.
        
        Args:
            name: Score name (e.g., "primary", "task_completion").
            value: Numeric score value.
            trace_id: OTEL trace ID to link the score to.
            observation_id: Optional span ID to link to specific observation.
            rollout_id: Optional rollout ID for metadata.
            attempt_id: Optional attempt ID for metadata.
        """
        score_payload: Dict[str, Any] = {
            "name": name,
            "value": value,
            "dataType": "NUMERIC",
            "traceId": trace_id,
        }
        
        if observation_id:
            score_payload["observationId"] = observation_id
        
        # Add rollout/attempt context as metadata
        metadata: Dict[str, Any] = {
            "source": "agent_lightning",
            "job_id": self._job_id,
        }
        if rollout_id:
            metadata["rollout_id"] = rollout_id
        if attempt_id:
            metadata["attempt_id"] = attempt_id
        score_payload["metadata"] = metadata

        # Create Basic auth header
        auth_string = f"{self._api_key}:{self._secret_key}"
        auth_bytes = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        # Send score in a non-blocking way (fire and forget with retries)
        def send_score_async() -> None:
            for attempt in range(self._max_retries):
                try:
                    with httpx.Client(timeout=self._request_timeout) as client:
                        response = client.post(
                            f"{self._insight_url}/api/public/scores",
                            headers={
                                "Authorization": f"Basic {auth_bytes}",
                                "Content-Type": "application/json",
                            },
                            json=score_payload,
                        )
                        response.raise_for_status()
                        logger.debug(f"Successfully sent score '{name}={value}' to Insight")
                        return
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        logger.error("Unauthorized (401) sending score to Insight. Check API credentials.")
                        return
                    else:
                        try:
                            error_body = e.response.json()
                        except Exception:
                            error_body = e.response.text
                        logger.warning(
                            f"HTTP error sending score (attempt {attempt + 1}/{self._max_retries}): "
                            f"{e.response.status_code} - {error_body}"
                        )
                except httpx.HTTPError as e:
                    logger.warning(f"Failed to send score (attempt {attempt + 1}/{self._max_retries}): {e}")

                # Exponential backoff
                if attempt < self._max_retries - 1:
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)

            logger.error(f"Failed to send score '{name}' after {self._max_retries} retries")

        # Run in a thread to avoid blocking
        threading.Thread(target=send_score_async, daemon=True, name="insight-score-sender").start()

    # ─────────────────────────────────────────────────────────────
    # Background Sender Thread
    # ─────────────────────────────────────────────────────────────

    def _start_sender_thread(self) -> None:
        """Start the background sender thread."""

        def sender_loop() -> None:
            while not self._stop_event.is_set():
                # Wait for the flush interval or until stopped
                self._stop_event.wait(timeout=self._flush_interval)
                if not self._stop_event.is_set():
                    self._flush_events()

        self._sender_thread = threading.Thread(
            target=sender_loop,
            daemon=True,
            name="insight-sender",
        )
        self._sender_thread.start()

    def _trigger_flush(self) -> None:
        """Trigger an immediate flush by interrupting the wait."""
        # The flush will happen on the next iteration since we're using a timeout
        pass

    def _flush_events(self) -> None:
        """Flush all buffered events to the Insight API."""
        events: List[InsightEvent] = []

        # Drain the queue
        while True:
            try:
                event = self._event_buffer.get_nowait()
                events.append(event)
            except queue.Empty:
                break

        if not events:
            return

        self._send_events(events)

    def _send_events(self, events: List[InsightEvent]) -> None:
        """Send events to the Insight API with retry logic."""
        if not events:
            return

        payload = {
            "job_id": self._job_id,
            # Note: project_id is not sent - it's derived from the API key auth
            "events": [
                {
                    "id": e.id,
                    "type": e.type,
                    "timestamp": e.timestamp,
                    "data": e.data,
                }
                for e in events
            ],
        }

        # Create Basic auth header from api_key:secret_key
        auth_string = f"{self._api_key}:{self._secret_key}"
        auth_bytes = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        for attempt in range(self._max_retries):
            try:
                with httpx.Client(timeout=self._request_timeout) as client:
                    response = client.post(
                        f"{self._insight_url}/api/public/v1/agent/ingest",
                        headers={
                            "Authorization": f"Basic {auth_bytes}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    response.raise_for_status()
                    logger.debug(f"Successfully sent {len(events)} events to Insight")
                    return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Unauthorized - bad API key, won't fix itself
                    logger.error("Unauthorized (401) sending events to Insight. Check API credentials.")
                    return
                elif e.response.status_code == 429:
                    # Rate limited - back off
                    logger.warning("Rate limited (429) sending events, retrying with backoff...")
                else:
                    # Log the full response for debugging
                    try:
                        error_body = e.response.json()
                    except Exception:
                        error_body = e.response.text
                    logger.warning(
                        f"HTTP error sending events (attempt {attempt + 1}/{self._max_retries}): "
                        f"{e.response.status_code} - {error_body}"
                    )
            except httpx.HTTPError as e:
                logger.warning(f"Failed to send events (attempt {attempt + 1}/{self._max_retries}): {e}")

            # Exponential backoff
            if attempt < self._max_retries - 1:
                backoff_time = 2**attempt
                time.sleep(backoff_time)

        logger.error(f"Failed to send {len(events)} events after {self._max_retries} retries - events dropped")

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Methods
    # ─────────────────────────────────────────────────────────────

    def complete(self, summary: Optional[Dict[str, Any]] = None) -> None:
        """Mark the job as complete and flush all remaining events."""
        if self._completed:
            return
        self._completed = True
        self._emit("job.completed", {"summary": summary or {}})
        self._stop_event.set()
        self._flush_events()
        logger.info(f"InsightTracker job {self._job_id} completed")

    def fail(self, error: str) -> None:
        """Mark the job as failed and flush all remaining events."""
        self._emit("job.failed", {"error": error})
        self._stop_event.set()
        self._flush_events()
        logger.error(f"InsightTracker job {self._job_id} failed: {error}")

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        if not self._stop_event.is_set():
            # Flush any remaining events before exiting
            self._flush_events()
            self._stop_event.set()

    def __enter__(self) -> "InsightTracker":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        if exc_type:
            self.fail(str(exc_val) if exc_val else "Unknown error")
        elif not self._completed:
            self.complete()


# ─────────────────────────────────────────────────────────────────────────────
# Convenience class for backward compatibility
# ─────────────────────────────────────────────────────────────────────────────


def InsightLightningStore(
    *,
    api_key: str,
    secret_key: str,
    insight_url: str,
    project_id: str,
    flush_interval: float = 1.0,
    max_buffer_size: int = 1000,
    request_timeout: float = 10.0,
    max_retries: int = 3,
    thread_safe: bool = False,
    **kwargs: Any,
) -> "InMemoryLightningStore":
    """Create an InMemoryLightningStore with Insight tracking enabled.

    This is a convenience function that creates an InsightTracker and attaches
    it to an InMemoryLightningStore. For more control, use InsightTracker directly.

    Args:
        api_key: Insight public API key for authentication.
        secret_key: Insight secret key for authentication.
        insight_url: Insight server URL (e.g., "http://localhost:3000").
        project_id: Project ID to associate events with.
        flush_interval: Seconds between automatic flushes (default: 1.0).
        max_buffer_size: Maximum events before forcing a flush (default: 1000).
        request_timeout: HTTP request timeout in seconds (default: 10.0).
        max_retries: Maximum retry attempts for failed requests (default: 3).
        thread_safe: Whether the underlying store is thread-safe (default: False).

    Returns:
        An InMemoryLightningStore with InsightTracker attached.

    Example:
        ```python
        store = InsightLightningStore(
            api_key="pk-lf-abc123",
            secret_key="sk-lf-xyz789",
            insight_url="https://insight.withmetis.ai",
            project_id="proj-123",
        )

        trainer = Trainer(algorithm=GEPA(...), store=store)
        ```
    """
    from .memory import InMemoryLightningStore as MemStore

    tracker = InsightTracker(
        api_key=api_key,
        secret_key=secret_key,
        insight_url=insight_url,
        project_id=project_id,
        flush_interval=flush_interval,
        max_buffer_size=max_buffer_size,
        request_timeout=request_timeout,
        max_retries=max_retries,
    )

    return MemStore(thread_safe=thread_safe, listeners=[tracker], **kwargs)
