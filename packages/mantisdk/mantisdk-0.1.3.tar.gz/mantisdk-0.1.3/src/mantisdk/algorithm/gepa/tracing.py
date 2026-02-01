# Copyright (c) Microsoft. All rights reserved.

"""GEPA-specific tracing context for detailed execution tracking.

This module provides a context class that tracks GEPA's execution state
(generation, phase, candidate, batch) to enable rich tagging of traces.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class GEPATracingContext:
    """Tracks execution state for detailed tracing in GEPA optimization.
    
    This class maintains state about the current phase of GEPA execution,
    generation/iteration number, and batch counts to enable rich tagging
    of traces for filtering and analysis in Mantis.
    
    GEPA-specific phases:
    - "train-eval": Evaluating candidates on training data
    - "validation-eval": Evaluating candidates on validation data  
    - "reflection": LLM reflection to improve prompts (distinct from validation!)
    
    Example:
        >>> ctx = GEPATracingContext()
        >>> ctx.generation
        0
        >>> ctx.session_id  # Auto-generated for grouping traces
        'gepa-abc123def456'
        >>> ctx.next_generation()
        >>> ctx.generation
        1
        >>> batch_id = ctx.next_batch()
        >>> batch_id
        'batch-1'
    
    Attributes:
        generation: Current generation/iteration number (0-indexed).
        phase: Current execution phase.
        candidate_id: Short hash of the current candidate being evaluated.
        batch_count: Number of batches processed in current generation.
        training_item_ids: Set of item IDs seen during training (for validation detection).
        session_id: Unique session identifier for grouping all traces in this GEPA run.
    """
    
    generation: int = 0
    phase: str = "train-eval"
    candidate_id: Optional[str] = None
    batch_count: int = 0
    training_item_ids: Set[str] = field(default_factory=set)
    session_id: str = field(default_factory=lambda: f"gepa-{uuid.uuid4().hex[:12]}")
    
    def next_batch(self) -> str:
        """Increment batch count and return batch identifier.
        
        Returns:
            Batch identifier string (e.g., "batch-1").
        """
        self.batch_count += 1
        return f"batch-{self.batch_count}"
    
    def set_phase(self, phase: str) -> None:
        """Set the current execution phase.
        
        Args:
            phase: Phase name (e.g., "train-eval", "validation-eval", "reflection").
        """
        self.phase = phase
    
    def next_generation(self) -> None:
        """Increment generation counter and reset batch count."""
        self.generation += 1
        self.batch_count = 0
    
    def set_candidate(self, candidate_id: str) -> None:
        """Set the current candidate identifier.
        
        Args:
            candidate_id: Short hash or identifier for the candidate.
        """
        self.candidate_id = candidate_id
    
    def register_training_items(self, item_ids: List[str]) -> None:
        """Register item IDs as training data for validation detection.
        
        Args:
            item_ids: List of item IDs from the training batch.
        """
        self.training_item_ids.update(item_ids)
    
    def is_validation_batch(self, item_ids: List[str]) -> bool:
        """Check if a batch contains validation items (not in training set).
        
        Args:
            item_ids: List of item IDs from the batch.
        
        Returns:
            True if any item is not in the training set.
        """
        if not self.training_item_ids:
            return False
        return any(item_id not in self.training_item_ids for item_id in item_ids)
