"""P1 Dynamic Memory — B03 SQLite persistence layer.

Implements atomic capture, append-only revision, and version retrieval.
The database schema is authoritative; this module does not create or
modify schema objects.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from .contracts import (
    ActivityEvent,
    CaptureRequest,
    CaptureResult,
    KnowledgeType,
    EpistemicStatus,
    VerificationStatus,
    ProvenanceRecord,
    RelationshipRecord,
    RetrievedMemory,
    calculate_content_hash,
)


class MemoryStore:
    """SQLite persistence operations for P1 Dynamic Memory."""

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "data" / "dm_memory.db"

        self.db_path = Path(db_path).resolve()

        if not self.db_path.is_file():
            raise FileNotFoundError(
                f"Database does not exist: {self.db_path}"
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_db_datetime(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise ValueError("Naive datetime cannot be persisted")
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _from_db_datetime(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            raise ValueError("Stored datetime is missing timezone")
        return parsed.astimezone(timezone.utc)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if enabled != 1:
            connection.close()
            raise RuntimeError(
                "SQLite foreign key enforcement is not enabled"
            )

        return connection

    @staticmethod
    def _validate_source_id(source_id: str) -> None:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")

    @staticmethod
    def _insert_version(
        connection: sqlite3.Connection,
        *,
        version_id: UUID,
        atom_id: UUID,
        version_no: int,
        request: CaptureRequest,
        created_at: datetime,
        supersedes_version_id: Optional[UUID],
    ) -> str:
        content_hash = calculate_content_hash(request.content)

        connection.execute(
            """
            INSERT INTO atom_versions (
                version_id,
                atom_id,
                version_no,
                content,
                content_hash,
                knowledge_type,
                epistemic_status,
                verification_status,
                valid_from,
                valid_until,
                created_at,
                supersedes_version_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(version_id),
                str(atom_id),
                version_no,
                request.content,
                content_hash,
                request.knowledge_type.value,
                request.epistemic_status.value,
                request.verification_status.value,
                MemoryStore._to_db_datetime(request.valid_from),
                MemoryStore._to_db_datetime(request.valid_until),
                MemoryStore._to_db_datetime(created_at),
                (
                    str(supersedes_version_id)
                    if supersedes_version_id is not None
                    else None
                ),
            ),
        )

        return content_hash

    @staticmethod
    def _insert_provenance(
        connection: sqlite3.Connection,
        *,
        provenance_id: UUID,
        version_id: UUID,
        request: CaptureRequest,
        source_id: str,
        captured_at: datetime,
    ) -> None:
        connection.execute(
            """
            INSERT INTO provenance (
                provenance_id,
                version_id,
                source_type,
                source_id,
                source_locator,
                source_created_at,
                captured_at,
                source_content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(provenance_id),
                str(version_id),
                request.source_type,
                source_id,
                request.source_locator,
                None,
                MemoryStore._to_db_datetime(captured_at),
                None,
            ),
        )

    @staticmethod
    def _insert_activity(
        connection: sqlite3.Connection,
        *,
        event_id: UUID,
        event_type: str,
        occurred_at: datetime,
        atom_id: UUID,
        version_id: UUID,
        details: dict,
    ) -> None:
        connection.execute(
            """
            INSERT INTO activity_events (
                event_id,
                event_type,
                occurred_at,
                atom_id,
                version_id,
                details_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(event_id),
                event_type,
                MemoryStore._to_db_datetime(occurred_at),
                str(atom_id),
                str(version_id),
                json.dumps(
                    details,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )

    def capture(
        self,
        request: CaptureRequest,
        *,
        source_id: str,
    ) -> CaptureResult:
        """Persist a first memory version and its provenance atomically."""
        self._validate_source_id(source_id)

        atom_id = uuid4()
        version_id = uuid4()
        provenance_id = uuid4()
        event_id = uuid4()
        now = self._now()

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            connection.execute(
                """
                INSERT INTO atoms (atom_id, created_at)
                VALUES (?, ?)
                """,
                (
                    str(atom_id),
                    self._to_db_datetime(now),
                ),
            )

            content_hash = self._insert_version(
                connection,
                version_id=version_id,
                atom_id=atom_id,
                version_no=1,
                request=request,
                created_at=now,
                supersedes_version_id=None,
            )

            self._insert_provenance(
                connection,
                provenance_id=provenance_id,
                version_id=version_id,
                request=request,
                source_id=source_id,
                captured_at=now,
            )

            self._insert_activity(
                connection,
                event_id=event_id,
                event_type="memory_captured",
                occurred_at=now,
                atom_id=atom_id,
                version_id=version_id,
                details={
                    "version_no": 1,
                    "source_type": request.source_type,
                },
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return CaptureResult(
            atom_id=atom_id,
            version_id=version_id,
            version_no=1,
            content_hash=content_hash,
            persisted_at=now,
            provenance_ids=[provenance_id],
        )

    def revise(
        self,
        atom_id: UUID,
        request: CaptureRequest,
        *,
        source_id: str,
    ) -> CaptureResult:
        """Append a new immutable version to an existing atom."""
        self._validate_source_id(source_id)

        version_id = uuid4()
        provenance_id = uuid4()
        event_id = uuid4()
        now = self._now()

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            previous = connection.execute(
                """
                SELECT version_id, version_no
                FROM atom_versions
                WHERE atom_id = ?
                ORDER BY version_no DESC
                LIMIT 1
                """,
                (str(atom_id),),
            ).fetchone()

            if previous is None:
                raise ValueError(
                    f"No existing memory found for atom_id: {atom_id}"
                )

            previous_version_id = UUID(previous["version_id"])
            next_version_no = previous["version_no"] + 1

            content_hash = self._insert_version(
                connection,
                version_id=version_id,
                atom_id=atom_id,
                version_no=next_version_no,
                request=request,
                created_at=now,
                supersedes_version_id=previous_version_id,
            )

            self._insert_provenance(
                connection,
                provenance_id=provenance_id,
                version_id=version_id,
                request=request,
                source_id=source_id,
                captured_at=now,
            )

            self._insert_activity(
                connection,
                event_id=event_id,
                event_type="memory_revised",
                occurred_at=now,
                atom_id=atom_id,
                version_id=version_id,
                details={
                    "version_no": next_version_no,
                    "supersedes_version_id": str(previous_version_id),
                    "source_type": request.source_type,
                },
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return CaptureResult(
            atom_id=atom_id,
            version_id=version_id,
            version_no=next_version_no,
            content_hash=content_hash,
            persisted_at=now,
            provenance_ids=[provenance_id],
        )

    def add_relationship(
        self,
        from_version_id: UUID,
        to_version_id: UUID,
    ) -> RelationshipRecord:
        """Persist a disputes relationship between two existing versions."""
        if from_version_id == to_version_id:
            raise ValueError(
                "A version cannot have a disputes relationship with itself"
            )

        relation_id = uuid4()
        created_at = self._now()

        # Validate the application contract before persistence.
        record = RelationshipRecord(
            relation_id=relation_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            relation_type="disputes",
            created_at=created_at,
        )

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            source_exists = connection.execute(
                """
                SELECT 1
                FROM atom_versions
                WHERE version_id = ?
                """,
                (str(from_version_id),),
            ).fetchone()

            if source_exists is None:
                raise ValueError(
                    f"Source version does not exist: {from_version_id}"
                )

            target_exists = connection.execute(
                """
                SELECT 1
                FROM atom_versions
                WHERE version_id = ?
                """,
                (str(to_version_id),),
            ).fetchone()

            if target_exists is None:
                raise ValueError(
                    f"Target version does not exist: {to_version_id}"
                )

            connection.execute(
                """
                INSERT INTO atom_version_relations (
                    relation_id,
                    from_version_id,
                    to_version_id,
                    relation_type,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(record.relation_id),
                    str(record.from_version_id),
                    str(record.to_version_id),
                    record.relation_type,
                    self._to_db_datetime(record.created_at),
                ),
            )

            connection.commit()
            return record

        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise

        finally:
            connection.close()

    def get_relationships(
        self,
        version_id: UUID,
    ) -> list[RelationshipRecord]:
        """Retrieve relationships where a version is either endpoint."""
        connection = self._connect()

        try:
            rows = connection.execute(
                """
                SELECT
                    relation_id,
                    from_version_id,
                    to_version_id,
                    relation_type,
                    created_at
                FROM atom_version_relations
                WHERE from_version_id = ?
                   OR to_version_id = ?
                ORDER BY created_at ASC, relation_id ASC
                """,
                (str(version_id), str(version_id)),
            ).fetchall()

        finally:
            connection.close()

        return [
            RelationshipRecord(
                relation_id=UUID(row["relation_id"]),
                from_version_id=UUID(row["from_version_id"]),
                to_version_id=UUID(row["to_version_id"]),
                relation_type=row["relation_type"],
                created_at=self._from_db_datetime(row["created_at"]),
            )
            for row in rows
        ]

    def get_activity_events(
        self,
        *,
        atom_id: UUID | None = None,
        version_id: UUID | None = None,
    ) -> list[ActivityEvent]:
        """Retrieve activity events, optionally filtered by atom or version."""
        conditions = []
        parameters = []

        if atom_id is not None:
            conditions.append("atom_id = ?")
            parameters.append(str(atom_id))

        if version_id is not None:
            conditions.append("version_id = ?")
            parameters.append(str(version_id))

        query = """
            SELECT
                event_id,
                event_type,
                occurred_at,
                atom_id,
                version_id,
                details_json
            FROM activity_events
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY occurred_at, event_id"

        connection = self._connect()

        try:
            rows = connection.execute(query, parameters).fetchall()
        finally:
            connection.close()

        events = []

        for row in rows:
            event_id = row["event_id"]
            details_json = row["details_json"]

            if details_json is None:
                details = None
            else:
                try:
                    details = json.loads(details_json)
                except (json.JSONDecodeError, TypeError) as exc:
                    raise ValueError(
                        f"Invalid details_json for activity event {event_id}"
                    ) from exc

                if not isinstance(details, dict):
                    raise ValueError(
                        f"Activity event {event_id} details_json must decode to an object"
                    )

            events.append(
                ActivityEvent(
                    event_id=UUID(event_id),
                    event_type=row["event_type"],
                    occurred_at=self._from_db_datetime(row["occurred_at"]),
                    atom_id=UUID(row["atom_id"]) if row["atom_id"] else None,
                    version_id=(
                        UUID(row["version_id"]) if row["version_id"] else None
                    ),
                    details=details,
                )
            )

        return events
    def get_version(self, version_id: UUID) -> Optional[RetrievedMemory]:
        """Retrieve one immutable version and its provenance records."""
        connection = self._connect()

        try:
            row = connection.execute(
                """
                SELECT
                    atom_id,
                    version_id,
                    version_no,
                    content,
                    content_hash,
                    knowledge_type,
                    epistemic_status,
                    verification_status,
                    created_at
                FROM atom_versions
                WHERE version_id = ?
                """,
                (str(version_id),),
            ).fetchone()

            if row is None:
                return None

            provenance_rows = connection.execute(
                """
                SELECT
                    provenance_id,
                    version_id,
                    source_type,
                    source_id,
                    source_locator,
                    source_created_at,
                    captured_at,
                    source_content_hash
                FROM provenance
                WHERE version_id = ?
                ORDER BY captured_at, provenance_id
                """,
                (str(version_id),),
            ).fetchall()

        finally:
            connection.close()

        provenance_records = [
            ProvenanceRecord(
                provenance_id=UUID(item["provenance_id"]),
                version_id=UUID(item["version_id"]),
                source_type=item["source_type"],
                source_id=item["source_id"],
                source_locator=item["source_locator"],
                source_created_at=self._from_db_datetime(
                    item["source_created_at"]
                ),
                captured_at=self._from_db_datetime(item["captured_at"]),
                source_content_hash=item["source_content_hash"],
            )
            for item in provenance_rows
        ]

        content = row["content"]
        stored_hash = row["content_hash"]
        calculated_hash = calculate_content_hash(content)

        if calculated_hash != stored_hash:
            raise ValueError(
                f"Content hash mismatch for version {version_id}"
            )

        return RetrievedMemory(
            atom_id=UUID(row["atom_id"]),
            version_id=UUID(row["version_id"]),
            version_no=row["version_no"],
            content=content,
            content_hash=stored_hash,
            knowledge_type=KnowledgeType(row["knowledge_type"]),
            epistemic_status=EpistemicStatus(row["epistemic_status"]),
            verification_status=VerificationStatus(
                row["verification_status"]
            ),
            created_at=self._from_db_datetime(row["created_at"]),
            provenance=provenance_records,
        )


__all__ = ["MemoryStore"]