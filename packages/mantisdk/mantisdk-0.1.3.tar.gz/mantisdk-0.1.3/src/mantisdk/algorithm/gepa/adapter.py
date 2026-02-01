# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence, TypedDict

from mantisdk.algorithm.gepa.lib.core.adapter import EvaluationBatch, GEPAAdapter

from mantisdk.adapter import TraceAdapter
from mantisdk.reward import find_final_reward, get_rewards_from_span, find_reward_spans
from mantisdk.store.base import LightningStore
from mantisdk.types import NamedResources, PromptTemplate, Rollout, Span, TracingConfig

from .tracing import GEPATracingContext

logger = logging.getLogger(__name__)


class MantisdkDataInst(TypedDict):
    """Data instance for Mantisdk."""

    input: Dict[str, Any]
    id: Optional[str]


class MantisdkTrajectory(TypedDict):
    """Trajectory for Mantisdk.
    
    Captures the data needed for reflection:
    - original_input: The task input data
    - assistant_response: The final LLM response
    - feedback: Evaluation feedback including score and status
    - spans: Raw spans for detailed analysis
    """

    rollout_id: str
    original_input: Dict[str, Any]  # The task input
    assistant_response: str  # The final LLM response
    feedback: str  # Feedback including score and error info
    spans: List[Span]


class MantisdkRolloutOutput(TypedDict):
    """Rollout output for Mantisdk."""

    final_reward: Optional[float]
    status: str


# TypedDict for GEPA's expected reflective record format
MantisdkReflectiveRecord = TypedDict(
    "MantisdkReflectiveRecord",
    {
        "Inputs": str,
        "Generated Outputs": str,
        "Feedback": str,
    },
)


class MantisdkGEPAAdapter(
    GEPAAdapter[MantisdkDataInst, MantisdkTrajectory, MantisdkRolloutOutput]
):
    """Adapter to bridge GEPA with Mantisdk.
    
    This adapter:
    1. Evaluates candidates by creating rollouts in the LightningStore
    2. Waits for runners to execute the agent
    3. Collects spans and rewards
    4. Builds reflective datasets for GEPA's reflection mechanism
    """

    def __init__(
        self,
        store: LightningStore,
        loop: asyncio.AbstractEventLoop,
        resource_name: str,
        adapter: TraceAdapter,
        llm_proxy_resource: Any = None,
        rollout_batch_timeout: float = 600.0,
        tracing_config: Optional[TracingConfig] = None,
        tracing_context: Optional[GEPATracingContext] = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            store: The LightningStore instance.
            loop: The asyncio loop where the store and other async components are running.
            resource_name: The name of the resource to update (e.g., "prompt_template").
            adapter: The TraceAdapter to convert spans to messages (optional, for debugging).
            llm_proxy_resource: LLM resource from the proxy to include in resources.
            rollout_batch_timeout: Timeout for waiting for rollouts in seconds.
            tracing_config: Optional tracing configuration from the algorithm.
            tracing_context: Optional GEPA tracing context for detailed execution tracking.
        """
        self.store = store
        self.loop = loop
        self.resource_name = resource_name
        self.adapter = adapter
        self.llm_proxy_resource = llm_proxy_resource
        self.rollout_batch_timeout = rollout_batch_timeout
        self.tracing_config = tracing_config
        self.tracing_context = tracing_context

    def evaluate(
        self,
        batch: List[MantisdkDataInst],
        candidate: Dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch[MantisdkTrajectory, MantisdkRolloutOutput]:
        """Evaluate a candidate on a batch of data instances.

        This method bridges the synchronous GEPA call to the asynchronous Mantisdk execution.
        """
        # Run the async evaluation in the main loop and wait for result
        future = asyncio.run_coroutine_threadsafe(
            self._evaluate_async(batch, candidate, capture_traces), self.loop
        )
        return future.result(timeout=self.rollout_batch_timeout + 60)  # Add buffer to timeout

    async def _evaluate_async(
        self,
        batch: List[MantisdkDataInst],
        candidate: Dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch[MantisdkTrajectory, MantisdkRolloutOutput]:
        """Asynchronous evaluation logic."""
        # 1. Build resources from candidate
        resources: NamedResources = {}
        for key, value in candidate.items():
            resources[key] = PromptTemplate(template=value, engine="f-string")
        
        # Add the LLM resource if available
        if self.llm_proxy_resource is not None:
            resources["llm"] = self.llm_proxy_resource

        # Create a unique resource version for this evaluation
        candidate_version = f"gepa-{uuid.uuid4().hex[:8]}"
        await self.store.update_resources(candidate_version, resources)

        # 2. Enqueue rollouts for each item in the batch
        rollout_ids = []
        batch_inputs: Dict[str, Dict[str, Any]] = {}  # Map rollout_id -> original input
        
        # Prepare metadata from tracing config with detailed context
        metadata = None
        if self.tracing_config and self.tracing_context:
            # Generate candidate hash for tracking
            candidate_hash = hashlib.md5(str(candidate).encode()).hexdigest()[:8]
            self.tracing_context.set_candidate(candidate_hash)
            
            # Get batch item IDs for validation detection
            item_ids = [item.get("id", str(i)) for i, item in enumerate(batch)]
            
            # Detect if this is a validation batch
            if self.tracing_context.is_validation_batch(item_ids):
                self.tracing_context.set_phase("validation-eval")
            else:
                # Register training items on first batch of generation
                if self.tracing_context.batch_count == 0:
                    self.tracing_context.register_training_items(item_ids)
                self.tracing_context.set_phase("train-eval")
            
            # Get batch ID and build GEPA-specific tags
            batch_id = self.tracing_context.next_batch()
            gepa_tags = [
                f"gen-{self.tracing_context.generation}",
                f"candidate-{candidate_hash}",
                batch_id,
            ]
            metadata = self.tracing_config.to_detailed_metadata(
                phase=self.tracing_context.phase,
                extra_tags=gepa_tags,
            )
            logger.debug(
                f"Batch evaluation: session={self.tracing_context.session_id}, "
                f"phase={self.tracing_context.phase}, "
                f"gen={self.tracing_context.generation}, candidate={candidate_hash}, {batch_id}"
            )
        elif self.tracing_config:
            # Fallback to simple metadata if no context
            metadata = self.tracing_config.to_metadata("train")

        for item in batch:
            task_input = item["input"]
            res = await self.store.enqueue_rollout(
                input=task_input,
                mode="train",
                resources_id=candidate_version,
                metadata=metadata,
            )
            rollout_ids.append(res.rollout_id)
            batch_inputs[res.rollout_id] = task_input

        # 3. Wait for completion
        try:
            completed_rollouts = await self.store.wait_for_rollouts(
                rollout_ids=rollout_ids, timeout=self.rollout_batch_timeout
            )
        except Exception as e:
            logger.error(f"Error waiting for rollouts: {e}")
            # Return failure results for all items
            outputs: List[MantisdkRolloutOutput] = []
            trajectories: List[MantisdkTrajectory] = [] if capture_traces else None
            scores: List[float] = []
            
            for rollout_id in rollout_ids:
                outputs.append({"final_reward": 0.0, "status": "failed"})
                scores.append(0.0)
                if capture_traces:
                    trajectories.append({
                        "rollout_id": rollout_id,
                        "original_input": batch_inputs.get(rollout_id, {}),
                        "assistant_response": "",
                        "feedback": f"Rollout failed with error: {e}",
                        "spans": [],
                    })
            
            return EvaluationBatch(
                outputs=outputs,
                trajectories=trajectories,
                scores=scores,
            )

        # 4. Collect results
        outputs: List[MantisdkRolloutOutput] = []
        trajectories: List[MantisdkTrajectory] = [] if capture_traces else None
        scores: List[float] = []

        for rollout in completed_rollouts:
            # Query spans for this rollout
            spans = await self.store.query_spans(rollout.rollout_id)
            
            # Find final reward
            final_reward_val = find_final_reward(spans)
            if final_reward_val is None:
                final_reward_val = 0.0
            
            outputs.append({
                "final_reward": final_reward_val,
                "status": rollout.status,
            })
            scores.append(final_reward_val)
            
            if capture_traces:
                # Extract assistant response from spans
                assistant_response = self._extract_assistant_response(spans)
                
                # Build feedback string
                feedback = self._build_feedback(
                    final_reward_val, 
                    rollout.status, 
                    spans,
                    batch_inputs.get(rollout.rollout_id, {})
                )
                
                trajectories.append({
                    "rollout_id": rollout.rollout_id,
                    "original_input": batch_inputs.get(rollout.rollout_id, {}),
                    "assistant_response": assistant_response,
                    "feedback": feedback,
                    "spans": spans,
                })

        return EvaluationBatch(
            outputs=outputs,
            trajectories=trajectories,
            scores=scores,
        )

    def _extract_assistant_response(self, spans: List[Span]) -> str:
        """Extract the final assistant response from spans."""
        responses = []
        
        for span in spans:
            attrs = span.attributes if hasattr(span, 'attributes') else {}
            name = span.name if hasattr(span, 'name') else ""
            
            # Look for LLM completion spans
            if "chat" in name.lower() or "completion" in name.lower() or "llm" in name.lower():
                # Try different attribute keys for response content
                response_keys = [
                    "gen_ai.completion.0.content",
                    "gen_ai.response.content", 
                    "response.content",
                    "completion",
                ]
                for key in response_keys:
                    if key in attrs and attrs[key]:
                        responses.append(str(attrs[key]))
                        break
        
        if responses:
            return responses[-1]  # Return the last (final) response
        return "No assistant response found in spans"

    def _build_feedback(
        self, 
        reward: float, 
        status: str, 
        spans: List[Span],
        task_input: Dict[str, Any]
    ) -> str:
        """Build detailed feedback for reflection.
        
        For evaluation tasks, extracts human_score and llm_score from reward dimensions
        to provide specific feedback about prediction errors.
        """
        parts = []
        
        # Try to extract multi-dimensional reward data (human_score, llm_score)
        human_score = None
        llm_score = None
        
        reward_spans = find_reward_spans(spans)
        for span in reward_spans:
            rewards = get_rewards_from_span(span)
            for r in rewards:
                if r.name == "human_score":
                    human_score = r.value
                elif r.name == "llm_score":
                    llm_score = r.value
        
        # If we have both scores, provide detailed evaluation feedback
        if human_score is not None and llm_score is not None:
            diff = llm_score - human_score
            if abs(diff) < 0.1:
                parts.append(f"Good prediction: LLM scored {llm_score:.2f}, human scored {human_score:.2f} (close match).")
            elif diff > 0:
                parts.append(f"OVERESTIMATED: LLM scored {llm_score:.2f} but human scored {human_score:.2f}. "
                           f"The prompt caused the LLM to rate this {diff:.2f} points too high. "
                           "Consider adding stricter criteria or examples.")
            else:
                parts.append(f"UNDERESTIMATED: LLM scored {llm_score:.2f} but human scored {human_score:.2f}. "
                           f"The prompt caused the LLM to rate this {abs(diff):.2f} points too low. "
                           "Consider broadening the criteria or recognizing subtle details.")
        else:
            # Fallback to generic feedback
            if reward >= 0.9:
                parts.append(f"The task was completed successfully with a high score of {reward:.2f}.")
            elif reward >= 0.5:
                parts.append(f"The task was partially successful with a score of {reward:.2f}. There is room for improvement.")
            else:
                parts.append(f"The task failed or performed poorly with a score of {reward:.2f}. The prompt needs significant improvement.")
        
        # Add status info
        if status != "succeeded":
            parts.append(f"Rollout status: {status}.")
        
        # Look for error information in spans
        for span in spans:
            attrs = span.attributes if hasattr(span, 'attributes') else {}
            if "error" in str(attrs).lower():
                parts.append(f"Error detected in execution.")
                break
        
        # Add task context
        if task_input:
            if "expected_choice" in task_input:
                parts.append(f"Expected answer: {task_input['expected_choice']}")
            # Include humanScore from task if available (for debugging)
            if "humanScore" in task_input:
                parts.append(f"Expected human score: {task_input['humanScore']:.2f}")
        
        return " ".join(parts)

    def make_reflective_dataset(
        self,
        candidate: Dict[str, str],
        eval_batch: EvaluationBatch[MantisdkTrajectory, MantisdkRolloutOutput],
        components_to_update: List[str],
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        """Create a reflective dataset for GEPA's reflection mechanism.
        
        Returns data in GEPA's expected format:
        {
            "component_name": [
                {
                    "Inputs": str,           # Task input description
                    "Generated Outputs": str, # Model outputs
                    "Feedback": str           # Performance feedback
                },
                ...
            ]
        }
        """
        reflective_data: Dict[str, List[MantisdkReflectiveRecord]] = {
            component: [] for component in components_to_update
        }

        trajectories = eval_batch.trajectories
        if trajectories is None:
            logger.warning("No trajectories available for building reflective dataset")
            return reflective_data

        for i, traj in enumerate(trajectories):
            output = eval_batch.outputs[i]
            
            # Format the input as a readable string
            input_str = self._format_input(traj["original_input"])
            
            # Get the assistant response
            generated_output = traj["assistant_response"]
            
            # Get the feedback
            feedback = traj["feedback"]
            
            record: MantisdkReflectiveRecord = {
                "Inputs": input_str,
                "Generated Outputs": generated_output,
                "Feedback": feedback,
            }
            
            # Add to each component being updated
            for component in components_to_update:
                reflective_data[component].append(record)

        # Validate we have data
        for component in components_to_update:
            if len(reflective_data[component]) == 0:
                logger.warning(f"No reflective records for component {component}")

        return reflective_data

    def _format_input(self, task_input: Dict[str, Any]) -> str:
        """Format task input as a readable string for reflection."""
        if not task_input:
            return "No input available"
        
        # If it's a RoomSelectionTask-like structure
        if "task_input" in task_input:
            inner = task_input["task_input"]
            parts = []
            if "date" in inner:
                parts.append(f"Date: {inner['date']}")
            if "time" in inner:
                parts.append(f"Time: {inner['time']}")
            if "duration_min" in inner:
                parts.append(f"Duration: {inner['duration_min']} minutes")
            if "attendees" in inner:
                parts.append(f"Attendees: {inner['attendees']}")
            if "needs" in inner:
                parts.append(f"Needs: {', '.join(inner['needs']) if inner['needs'] else 'none'}")
            if "accessible_required" in inner:
                parts.append(f"Accessible required: {inner['accessible_required']}")
            return "; ".join(parts) if parts else json.dumps(task_input)
        
        # For other dict structures, try to format nicely
        try:
            if len(task_input) <= 5:
                return "; ".join(f"{k}: {v}" for k, v in task_input.items())
            return json.dumps(task_input, indent=2)
        except Exception:
            return str(task_input)
