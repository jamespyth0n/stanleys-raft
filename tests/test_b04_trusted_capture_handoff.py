"""Gate 3 trusted extraction-to-capture handoff tests."""

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from dynamic_memory.application import (
    DynamicMemoryApplication,
    ExtractionCandidate,
)
from dynamic_memory.application.capture_service import CaptureService
from dynamic_memory.contracts import (
    CaptureRequest,
    VerificationStatus,
)
from dynamic_memory.persistence import MemoryStore


class CaptureSpy:
    def __init__(self):
        self.calls = []
        self.result = object()

    def capture(self, request, *, source_id):
        self.calls.append((request, source_id))
        return self.result


def make_candidate(**overrides):
    values = {
        "content": "The extracted proposal.",
        "knowledge_type": "fact",
        "epistemic_status": "observed",
        "valid_from": None,
        "valid_until": None,
    }
    values.update(overrides)
    return ExtractionCandidate(**values)


def initialize_test_database(db_path):
    """Initialize a temporary DB from the authoritative B03 schema."""
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "dynamic_memory"
        / "schema.sql"
    )
    schema = schema_path.read_text(encoding="utf-8")

    connection = sqlite3.connect(str(db_path))
    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()


class TestTrustedCaptureHandoff(unittest.TestCase):

    def test_candidate_is_converted_to_existing_capture_request(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )
        candidate = make_candidate()

        result = app.capture_candidate(
            candidate=candidate,
            source_id="trusted-source-001",
            source_type="user_provided",
            source_locator="conversation/message-1",
        )

        self.assertIs(result, spy.result)
        self.assertEqual(len(spy.calls), 1)

        request, source_id = spy.calls[0]
        self.assertIsInstance(request, CaptureRequest)
        self.assertEqual(request.content, candidate.content)
        self.assertEqual(request.knowledge_type, candidate.knowledge_type)
        self.assertEqual(request.epistemic_status, candidate.epistemic_status)
        self.assertEqual(source_id, "trusted-source-001")

    def test_verification_status_is_forced_to_unverified(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )

        app.capture_candidate(
            candidate=make_candidate(),
            source_id="trusted-source-002",
            source_type="user_provided",
        )

        request, _ = spy.calls[0]
        self.assertEqual(
            request.verification_status,
            VerificationStatus.UNVERIFIED,
        )

    def test_trusted_provenance_is_not_taken_from_candidate(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )

        app.capture_candidate(
            candidate=make_candidate(),
            source_id="application-source",
            source_type="application_input",
            source_locator="trusted://locator",
        )

        request, source_id = spy.calls[0]
        self.assertEqual(source_id, "application-source")
        self.assertEqual(request.source_type, "application_input")
        self.assertEqual(request.source_locator, "trusted://locator")

    def test_temporal_bounds_are_preserved(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )
        valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        valid_until = datetime(2026, 12, 31, tzinfo=timezone.utc)

        app.capture_candidate(
            candidate=make_candidate(
                valid_from=valid_from,
                valid_until=valid_until,
            ),
            source_id="trusted-source-003",
            source_type="user_provided",
        )

        request, _ = spy.calls[0]
        self.assertEqual(request.valid_from, valid_from)
        self.assertEqual(request.valid_until, valid_until)

    def test_wrong_candidate_type_is_rejected_before_capture(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )

        with self.assertRaises(TypeError):
            app.capture_candidate(
                candidate={"content": "unvalidated"},
                source_id="trusted-source",
                source_type="user_provided",
            )

        self.assertEqual(spy.calls, [])

    def test_blank_trusted_source_type_is_rejected_before_capture(self):
        spy = CaptureSpy()
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=spy,
        )

        with self.assertRaises(ValueError):
            app.capture_candidate(
                candidate=make_candidate(),
                source_id="trusted-source",
                source_type="   ",
            )

        self.assertEqual(spy.calls, [])

    def test_whitespace_source_type_is_rejected_by_direct_capture_service(self):
        store = CaptureSpy()
        service = CaptureService(store=store)
        candidate = make_candidate()

        request = CaptureRequest(
            content=candidate.content,
            knowledge_type=candidate.knowledge_type,
            epistemic_status=candidate.epistemic_status,
            source_type="   ",
        )

        with self.assertRaises(ValueError):
            service.capture(
                request=request,
                source_id="trusted-source",
            )

        self.assertEqual(store.calls, [])

    def test_blank_source_id_is_rejected_by_real_capture_service(self):
        app = DynamicMemoryApplication(
            store=object(),
            capture_service=CaptureService(store=object()),
        )

        with self.assertRaises(ValueError):
            app.capture_candidate(
                candidate=make_candidate(),
                source_id="   ",
                source_type="user_provided",
            )

    def test_real_b03_persistence_preserves_trusted_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "trusted_handoff.db"
            initialize_test_database(db_path)

            store = MemoryStore(db_path=db_path)
            app = DynamicMemoryApplication(store=store)

            result = app.capture_candidate(
                candidate=make_candidate(
                    content="Persisted from an explicitly approved proposal."
                ),
                source_id="architect-approved-source",
                source_type="user_provided",
                source_locator="conversation/approved-message",
            )

            retrieved = app.get_version(version_id=result.version_id)

            self.assertIsNotNone(retrieved)
            self.assertEqual(
                retrieved.content,
                "Persisted from an explicitly approved proposal.",
            )
            self.assertEqual(
                retrieved.verification_status,
                VerificationStatus.UNVERIFIED,
            )
            self.assertEqual(len(retrieved.provenance), 1)

            provenance = retrieved.provenance[0]
            self.assertEqual(
                provenance.source_id,
                "architect-approved-source",
            )
            self.assertEqual(
                provenance.source_type,
                "user_provided",
            )
            self.assertEqual(
                provenance.source_locator,
                "conversation/approved-message",
            )

            self.assertEqual(
                retrieved.version_id,
                result.version_id,
            )
            self.assertEqual(
                retrieved.atom_id,
                result.atom_id,
            )
            self.assertEqual(
                retrieved.content_hash,
                result.content_hash,
            )


if __name__ == "__main__":
    unittest.main()