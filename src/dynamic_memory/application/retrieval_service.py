"""Application boundary for B03 retrieval operations."""

from uuid import UUID
from typing import Optional

from dynamic_memory.contracts import (
    ActivityEvent,
    RelationshipRecord,
    RetrievedMemory,
)
from dynamic_memory.persistence import MemoryStore


class RetrievalService:
    def __init__(self, store: MemoryStore):
        self._store = store

    def get_version(self, *, version_id: UUID) -> Optional[RetrievedMemory]:
        if not isinstance(version_id, UUID):
            raise TypeError("version_id must be a UUID.")

        return self._store.get_version(version_id)

    def get_relationships(
        self,
        *,
        version_id: UUID,
    ) -> list[RelationshipRecord]:
        if not isinstance(version_id, UUID):
            raise TypeError("version_id must be a UUID.")

        return self._store.get_relationships(version_id)

    def get_activity_events(
        self,
        *,
        atom_id: Optional[UUID] = None,
        version_id: Optional[UUID] = None,
    ) -> list[ActivityEvent]:
        if atom_id is not None and not isinstance(atom_id, UUID):
            raise TypeError("atom_id must be a UUID or None.")

        if version_id is not None and not isinstance(version_id, UUID):
            raise TypeError("version_id must be a UUID or None.")

        return self._store.get_activity_events(
            atom_id=atom_id,
            version_id=version_id,
        )