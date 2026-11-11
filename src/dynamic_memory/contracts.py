"""P1 Dynamic Memory — B03 application contracts.

Pydantic V2 contracts for memory capture, persistence,
retrieval, provenance, relationships and model outcomes.
"""

from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------

class KnowledgeType(str, Enum):
    FACT = "fact"
    OBSERVATION = "observation"
    PREFERENCE = "preference"
    CONCEPT = "concept"
    QUESTION = "question"
    INTENTION = "intention"
    PROCEDURE = "procedure"
    HYPOTHESIS = "hypothesis"
    CONCLUSION = "conclusion"


class EpistemicStatus(str, Enum):
    ASSERTED = "asserted"
    OBSERVED = "observed"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"
    CONCLUDED = "concluded"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CHALLENGED = "challenged"


# ---------------------------------------------------------
# Base contract
# ---------------------------------------------------------

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def validate_uuidv4_and_normalize_datetime(cls, value: Any) -> Any:
        """Enforce UUIDv4 values and normalize aware datetimes to UTC."""
        if isinstance(value, datetime):
            if value.utcoffset() is None:
                raise ValueError(
                    "Datetime must include timezone information"
                )
            return value.astimezone(timezone.utc)

        if isinstance(value, UUID):
            if value.version != 4:
                raise ValueError("UUID must be version 4")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, UUID) and item.version != 4:
                    raise ValueError("UUID values must be version 4")

        return value


# ---------------------------------------------------------
# 1. ProvenanceRecord
# ---------------------------------------------------------

class ProvenanceRecord(Contract):
    provenance_id: UUID
    version_id: UUID

    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_locator: str | None = None

    source_created_at: datetime | None = None
    captured_at: datetime

    source_content_hash: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )


# ---------------------------------------------------------
# 2. CaptureRequest
# ---------------------------------------------------------

class CaptureRequest(Contract):
    content: str = Field(min_length=1)

    knowledge_type: KnowledgeType
    epistemic_status: EpistemicStatus

    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    )

    source_type: str = Field(min_length=1)
    source_locator: str | None = None

    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @model_validator(mode="after")
    def validate_interval(self):
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise ValueError(
                "valid_until precedes valid_from"
            )

        return self


# ---------------------------------------------------------
# 3. CaptureResult
# ---------------------------------------------------------

class CaptureResult(Contract):
    atom_id: UUID
    version_id: UUID

    version_no: int = Field(ge=1)
    content_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    persisted_at: datetime
    provenance_ids: list[UUID] = Field(min_length=1)


# ---------------------------------------------------------
# 4. RetrievedMemory
# ---------------------------------------------------------

class RetrievedMemory(Contract):
    atom_id: UUID
    version_id: UUID
    version_no: int = Field(ge=1)

    content: str
    content_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    knowledge_type: KnowledgeType
    epistemic_status: EpistemicStatus
    verification_status: VerificationStatus

    created_at: datetime
    provenance: list[ProvenanceRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_provenance_version(self) -> "RetrievedMemory":
        for record in self.provenance:
            if record.version_id != self.version_id:
                raise ValueError(
                    "Provenance version_id must match the parent memory version_id"
                )
        return self


# ---------------------------------------------------------
# 5. RelationshipRecord
# ---------------------------------------------------------

class RelationshipRecord(Contract):
    relation_id: UUID
    from_version_id: UUID
    to_version_id: UUID

    relation_type: Literal["disputes"]

    created_at: datetime


# ---------------------------------------------------------
# 6. ActivityEvent
# ---------------------------------------------------------

class ActivityEvent(Contract):
    event_id: UUID
    event_type: str = Field(min_length=1)

    occurred_at: datetime

    atom_id: UUID | None = None
    version_id: UUID | None = None

    details: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_reference_pair(self):
        if (self.atom_id is None) != (
            self.version_id is None
        ):
            raise ValueError(
                "atom_id and version_id must be supplied together"
            )

        return self


# ---------------------------------------------------------
# 7. ContextItem
# ---------------------------------------------------------

class ContextItem(Contract):
    atom_id: UUID
    version_id: UUID

    content: str
    provenance: list[ProvenanceRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_provenance_version(self) -> "ContextItem":
        for record in self.provenance:
            if record.version_id != self.version_id:
                raise ValueError(
                    "Provenance version_id must match the parent memory version_id"
                )
        return self


# ---------------------------------------------------------
# 8. ModelResponseOutcome
# ---------------------------------------------------------

class ModelResponseOutcome(Contract):
    request_id: UUID

    model_name: str = Field(min_length=1)
    response_text: str

    retrieved_version_ids: list[UUID]

    completed_at: datetime

    success: bool
    error_type: str | None = None


# ---------------------------------------------------------
# Content integrity utility
# ---------------------------------------------------------

def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 from the exact UTF-8 content string."""
    return sha256(content.encode("utf-8")).hexdigest()


__all__ = [
    "KnowledgeType",
    "EpistemicStatus",
    "VerificationStatus",
    "Contract",
    "ProvenanceRecord",
    "CaptureRequest",
    "CaptureResult",
    "RetrievedMemory",
    "RelationshipRecord",
    "ActivityEvent",
    "ContextItem",
    "ModelResponseOutcome",
    "calculate_content_hash",
]