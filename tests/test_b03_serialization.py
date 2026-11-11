import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dynamic_memory.contracts import (
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
ATOM = uuid4()
VERSION = uuid4()
PROVENANCE_ID = uuid4()
CONTENT = "Round-trip test — memory 🦅"
CONTENT_HASH = calculate_content_hash(CONTENT)

PROVENANCE = ProvenanceRecord(
    provenance_id=PROVENANCE_ID,
    version_id=VERSION,
    source_type="conversation",
    source_id="serialization-test",
    source_locator="message-001",
    source_created_at=NOW,
    captured_at=NOW,
)

CONTRACTS = [
    ProvenanceRecord(
        provenance_id=PROVENANCE_ID,
        version_id=VERSION,
        source_type="conversation",
        source_id="serialization-test",
        source_locator="message-001",
        source_created_at=NOW,
        captured_at=NOW,
    ),
    CaptureRequest(
        content=CONTENT,
        knowledge_type="fact",
        epistemic_status="asserted",
        source_type="conversation",
        source_locator="message-001",
        valid_from=NOW,
    ),
    CaptureResult(
        atom_id=ATOM,
        version_id=VERSION,
        version_no=1,
        content_hash=CONTENT_HASH,
        persisted_at=NOW,
        provenance_ids=[PROVENANCE_ID],
    ),
    RetrievedMemory(
        atom_id=ATOM,
        version_id=VERSION,
        version_no=1,
        content=CONTENT,
        content_hash=CONTENT_HASH,
        knowledge_type="fact",
        epistemic_status="asserted",
        verification_status="unverified",
        created_at=NOW,
        provenance=[PROVENANCE],
    ),
    RelationshipRecord(
        relation_id=uuid4(),
        from_version_id=VERSION,
        to_version_id=uuid4(),
        relation_type="disputes",
        created_at=NOW,
    ),
    ActivityEvent(
        event_id=uuid4(),
        event_type="capture",
        occurred_at=NOW,
        atom_id=ATOM,
        version_id=VERSION,
        details={
            "source": "test",
            "attempt": 1,
            "flags": ["round-trip", "unicode"],
            "metadata": {"verified": False},
        },
    ),
    ContextItem(
        atom_id=ATOM,
        version_id=VERSION,
        content=CONTENT,
        provenance=[PROVENANCE],
    ),
    ModelResponseOutcome(
        request_id=uuid4(),
        model_name="test-model",
        response_text="Serialization test response",
        retrieved_version_ids=[VERSION],
        completed_at=NOW,
        success=True,
    ),
]


class TestB03Serialization(unittest.TestCase):

    def test_01_provenance_round_trip(self):
        original = CONTRACTS[0]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)

    def test_02_capture_request_round_trip(self):
        original = CONTRACTS[1]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)

    def test_03_capture_result_round_trip(self):
        original = CONTRACTS[2]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)

    def test_04_retrieved_memory_nested_round_trip(self):
        original = CONTRACTS[3]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)
        self.assertEqual(restored.provenance[0], PROVENANCE)

    def test_05_relationship_round_trip(self):
        original = CONTRACTS[4]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)

    def test_06_activity_event_nested_details_round_trip(self):
        original = CONTRACTS[5]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)
        self.assertEqual(
            restored.details["metadata"]["verified"],
            False,
        )
        self.assertEqual(
            restored.details["flags"],
            ["round-trip", "unicode"],
        )

    def test_07_context_item_nested_round_trip(self):
        original = CONTRACTS[6]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)
        self.assertEqual(restored.provenance[0], PROVENANCE)

    def test_08_model_response_outcome_round_trip(self):
        original = CONTRACTS[7]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored, original)

    def test_09_unicode_content_preserved(self):
        original = CONTRACTS[3]
        restored = type(original).model_validate_json(
            original.model_dump_json()
        )
        self.assertEqual(restored.content, CONTENT)
        self.assertEqual(
            calculate_content_hash(restored.content),
            CONTENT_HASH,
        )

    def test_10_json_output_is_valid_json(self):
        for contract in CONTRACTS:
            with self.subTest(contract=type(contract).__name__):
                json_text = contract.model_dump_json()
                self.assertIsInstance(json_text, str)
                self.assertTrue(json_text.startswith("{"))
                self.assertTrue(json_text.endswith("}"))


if __name__ == "__main__":
    unittest.main(verbosity=2)