from __future__ import annotations

"""B04 internal result structures.

These structures do not alter or extend B03 persistence contracts.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from dynamic_memory.contracts import (
    CaptureResult,
    ContextItem,
    ModelResponseOutcome,
    RetrievedMemory,
)


@dataclass(frozen=True)
class ContextAssemblyResult:
    success: bool
    context_items: Tuple[ContextItem, ...]
    included_version_ids: Tuple[UUID, ...]
    excluded_version_ids: Tuple[UUID, ...]
    total_characters: int
    error_type: Optional[str] = None


@dataclass(frozen=True)
class ModelResult:
    """Provider-neutral result of a model invocation."""

    success: bool
    response_text: str
    model_name: str
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class ExtractionResult:
    """Internal result of model-proposed knowledge extraction."""

    success: bool
    candidates: Tuple["ExtractionCandidate", ...] = ()
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class WorkflowResult:
    """B04-owned report of a multi-stage application workflow.

    Preserves completed stage results when a later stage fails.
    Does not extend or replace B03 persistence contracts.
    """

    success: bool
    capture_result: Optional[CaptureResult] = None
    retrieved_memory: Optional[RetrievedMemory] = None
    context_result: Optional[ContextAssemblyResult] = None
    response_outcome: Optional[ModelResponseOutcome] = None
    failed_stage: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
