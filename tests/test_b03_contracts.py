import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dynamic_memory.contracts import (
    KnowledgeType,
    EpistemicStatus,
    VerificationStatus,
    ProvenanceRecord,
    CaptureRequest,
    CaptureResult,
    RetrievedMemory,
    RelationshipRecord,
    ActivityEvent,
    ContextItem,
    ModelResponseOutcome,
    calculate_content_hash,
)

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
NAIVE = datetime(2026, 11, 10, 12, 0)
HASH = calculate_content_hash("Test memory")

ATOM = uuid4()
VERSION = uuid4()
PROVENANCE = uuid4()


class TestB03Contracts(unittest.TestCase):

    def test_01_provenance_record(self):
        item = ProvenanceRecord(
            provenance_id=PROVENANCE,
            version_id=VERSION,
            source_type="conversation",
            source_id="test-source",
            captured_at=NOW,
        )
        self.assertEqual(item.version_id, VERSION)

    def test_02_capture_request(self):
        item = CaptureRequest(
            content="Test memory",
            knowledge_type="fact",
            epistemic_status="asserted",
            source_type="conversation",
            valid_from=NOW,
        )
        self.assertEqual(item.knowledge_type, KnowledgeType.FACT)
        self.assertEqual(
            item.verification_status,
            VerificationStatus.UNVERIFIED
        )

    def test_03_capture_result(self):
        item = CaptureResult(
            atom_id=ATOM,
            version_id=VERSION,
            version_no=1,
            content_hash=HASH,
            persisted_at=NOW,
            provenance_ids=[PROVENANCE],
        )
        self.assertEqual(item.version_no, 1)

    def test_04_retrieved_memory(self):
        provenance = ProvenanceRecord(
            provenance_id=PROVENANCE,
            version_id=VERSION,
            source_type="conversation",
            source_id="test-source",
            captured_at=NOW,
        )
        item = RetrievedMemory(
            atom_id=ATOM,
            version_id=VERSION,
            version_no=1,
            content="Test memory",
            content_hash=HASH,
            knowledge_type="fact",
            epistemic_status="asserted",
            verification_status="unverified",
            created_at=NOW,
            provenance=[provenance],
        )
        self.assertEqual(len(item.provenance), 1)

    def test_05_relationship_record(self):
        item = RelationshipRecord(
            relation_id=uuid4(),
            from_version_id=VERSION,
            to_version_id=uuid4(),
            relation_type="disputes",
            created_at=NOW,
        )
        self.assertEqual(item.relation_type, "disputes")

    def test_06_activity_event(self):
        item = ActivityEvent(
            event_id=uuid4(),
            event_type="capture",
            occurred_at=NOW,
            atom_id=ATOM,
            version_id=VERSION,
            details={"source": "test"},
        )
        self.assertEqual(item.event_type, "capture")

    def test_07_context_item(self):
        provenance = ProvenanceRecord(
            provenance_id=PROVENANCE,
            version_id=VERSION,
            source_type="conversation",
            source_id="test-source",
            captured_at=NOW,
        )
        item = ContextItem(
            atom_id=ATOM,
            version_id=VERSION,
            content="Test memory",
            provenance=[provenance],
        )
        self.assertEqual(item.atom_id, ATOM)

    def test_08_model_response_outcome(self):
        item = ModelResponseOutcome(
            request_id=uuid4(),
            model_name="test-model",
            response_text="Test response",
            retrieved_version_ids=[VERSION],
            completed_at=NOW,
            success=True,
        )
        self.assertTrue(item.success)

    def test_09_invalid_uuid_rejected(self):
        with self.assertRaises(ValueError):
            CaptureResult(
                atom_id="not-a-uuid",
                version_id=VERSION,
                version_no=1,
                content_hash=HASH,
                persisted_at=NOW,
                provenance_ids=[],
            )

    def test_10_invalid_enum_rejected(self):
        with self.assertRaises(ValueError):
            CaptureRequest(
                content="Test",
                knowledge_type="imaginary",
                epistemic_status="asserted",
                source_type="test",
            )

    def test_11_extra_fields_rejected(self):
        with self.assertRaises(ValueError):
            CaptureRequest(
                content="Test",
                knowledge_type="fact",
                epistemic_status="asserted",
                source_type="test",
                unauthorized_field="unexpected",
            )

    def test_12_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            CaptureRequest(
                content="Test",
                knowledge_type="fact",
                epistemic_status="asserted",
                source_type="test",
                valid_from=NAIVE,
            )

    def test_13_datetime_normalized_to_utc(self):
        eastern = timezone(timedelta(hours=-5))
        local_time = datetime(
            2026, 11, 10, 7, 0, tzinfo=eastern
        )
        item = CaptureRequest(
            content="Test",
            knowledge_type="fact",
            epistemic_status="asserted",
            source_type="test",
            valid_from=local_time,
        )
        self.assertEqual(item.valid_from, NOW)
        self.assertEqual(
            item.valid_from.utcoffset(),
            timedelta(0)
        )

    def test_14_invalid_temporal_interval_rejected(self):
        with self.assertRaises(ValueError):
            CaptureRequest(
                content="Test",
                knowledge_type="fact",
                epistemic_status="asserted",
                source_type="test",
                valid_from=NOW,
                valid_until=datetime(
                    2026, 11, 9, 12, 0, tzinfo=timezone.utc
                ),
            )

    def test_15_invalid_relationship_type_rejected(self):
        with self.assertRaises(ValueError):
            RelationshipRecord(
                relation_id=uuid4(),
                from_version_id=VERSION,
                to_version_id=uuid4(),
                relation_type="supports",
                created_at=NOW,
            )

    def test_16_activity_reference_pair_rejected(self):
        with self.assertRaises(ValueError):
            ActivityEvent(
                event_id=uuid4(),
                event_type="capture",
                occurred_at=NOW,
                atom_id=ATOM,
                version_id=None,
            )

    def test_17_hash_format_rejected(self):
        with self.assertRaises(ValueError):
            CaptureResult(
                atom_id=ATOM,
                version_id=VERSION,
                version_no=1,
                content_hash="invalid",
                persisted_at=NOW,
                provenance_ids=[],
            )

    def test_18_hash_utility_exact_content(self):
        self.assertEqual(
            calculate_content_hash("Test memory"),
            HASH,
        )
        self.assertNotEqual(
            calculate_content_hash("Test memory "),
            HASH,
        )
        self.assertEqual(len(HASH), 64)

    def test_19_optional_datetime_none_accepted(self):
        item = CaptureRequest(
            content="Test",
            knowledge_type="fact",
            epistemic_status="asserted",
            source_type="test",
            valid_from=None,
            valid_until=None,
        )
        self.assertIsNone(item.valid_from)
        self.assertIsNone(item.valid_until)


if __name__ == "__main__":
    unittest.main(verbosity=2)