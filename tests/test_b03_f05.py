import unittest
from datetime import datetime, timezone
from uuid import uuid4

from dynamic_memory.contracts import (
    CaptureResult,
    ContextItem,
    RetrievedMemory,
    ProvenanceRecord,
)

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def make_provenance(version_id):
    return ProvenanceRecord(
        provenance_id=uuid4(),
        version_id=version_id,
        source_type="conversation",
        source_id="f05-test-source",
        captured_at=NOW,
    )


def make_retrieved_memory(version_id, provenance):
    return RetrievedMemory(
        atom_id=uuid4(),
        version_id=version_id,
        version_no=1,
        content="F-05 test memory",
        content_hash=HASH,
        knowledge_type="fact",
        epistemic_status="asserted",
        verification_status="unverified",
        created_at=NOW,
        provenance=provenance,
    )


class TestB03F05ProvenanceConsistency(unittest.TestCase):

    def test_capture_result_rejects_empty_provenance_ids(self):
        with self.assertRaises(ValueError):
            CaptureResult(
                atom_id=uuid4(),
                version_id=uuid4(),
                version_no=1,
                content_hash=HASH,
                persisted_at=NOW,
                provenance_ids=[],
            )

    def test_capture_result_accepts_provenance_id(self):
        result = CaptureResult(
            atom_id=uuid4(),
            version_id=uuid4(),
            version_no=1,
            content_hash=HASH,
            persisted_at=NOW,
            provenance_ids=[uuid4()],
        )
        self.assertEqual(len(result.provenance_ids), 1)

    def test_retrieved_memory_rejects_empty_provenance(self):
        with self.assertRaises(ValueError):
            make_retrieved_memory(uuid4(), [])

    def test_retrieved_memory_rejects_mismatched_version(self):
        parent_version = uuid4()
        wrong_version = uuid4()

        with self.assertRaises(ValueError):
            make_retrieved_memory(
                parent_version,
                [make_provenance(wrong_version)],
            )

    def test_retrieved_memory_accepts_matching_version(self):
        version_id = uuid4()
        item = make_retrieved_memory(
            version_id,
            [make_provenance(version_id)],
        )
        self.assertEqual(item.provenance[0].version_id, version_id)

    def test_context_item_rejects_empty_provenance(self):
        with self.assertRaises(ValueError):
            ContextItem(
                atom_id=uuid4(),
                version_id=uuid4(),
                content="F-05 context",
                provenance=[],
            )

    def test_context_item_rejects_mismatched_version(self):
        parent_version = uuid4()

        with self.assertRaises(ValueError):
            ContextItem(
                atom_id=uuid4(),
                version_id=parent_version,
                content="F-05 context",
                provenance=[make_provenance(uuid4())],
            )

    def test_context_item_accepts_matching_version(self):
        version_id = uuid4()
        item = ContextItem(
            atom_id=uuid4(),
            version_id=version_id,
            content="F-05 context",
            provenance=[make_provenance(version_id)],
        )
        self.assertEqual(item.provenance[0].version_id, version_id)


if __name__ == "__main__":
    unittest.main()