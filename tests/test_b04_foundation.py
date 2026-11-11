"""B04 deterministic foundation tests."""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from dynamic_memory.contracts import (
    CaptureRequest,
    CaptureResult,
    ContextItem,
    EpistemicStatus,
    KnowledgeType,
    ProvenanceRecord,
    RetrievedMemory,
    VerificationStatus,
)
from dynamic_memory.application.capture_service import CaptureService
from dynamic_memory.application.context_assembler import ContextAssembler
from dynamic_memory.application.entry import DynamicMemoryApplication
from dynamic_memory.application.retrieval_service import RetrievalService


def make_memory(content="memory content"):
    atom_id = uuid4()
    version_id = uuid4()
    provenance = ProvenanceRecord(
        provenance_id=uuid4(),
        version_id=version_id,
        source_type="test",
        source_id="test-source",
        captured_at=datetime.now(timezone.utc),
    )
    return RetrievedMemory(
        atom_id=atom_id,
        version_id=version_id,
        version_no=1,
        content=content,
        content_hash="a" * 64,
        knowledge_type=KnowledgeType.FACT,
        epistemic_status=EpistemicStatus.OBSERVED,
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=datetime.now(timezone.utc),
        provenance=[provenance],
    )


def make_request():
    return CaptureRequest(
        content="A test fact.",
        knowledge_type=KnowledgeType.FACT,
        epistemic_status=EpistemicStatus.OBSERVED,
        verification_status=VerificationStatus.UNVERIFIED,
        source_type="test",
    )


class TestB04CaptureService(unittest.TestCase):
    def test_delegates_to_b03_with_trusted_source_id(self):
        store = Mock()
        expected = Mock(spec=CaptureResult)
        store.capture.return_value = expected

        service = CaptureService(store)
        request = make_request()

        result = service.capture(
            request=request,
            source_id="trusted-source",
        )

        self.assertIs(result, expected)
        store.capture.assert_called_once_with(
            request,
            source_id="trusted-source",
        )

    def test_rejects_blank_source_id(self):
        store = Mock()
        service = CaptureService(store)

        with self.assertRaises(ValueError):
            service.capture(request=make_request(), source_id="  ")

        store.capture.assert_not_called()

    def test_rejects_wrong_request_type(self):
        store = Mock()
        service = CaptureService(store)

        with self.assertRaises(TypeError):
            service.capture(request={}, source_id="trusted-source")

        store.capture.assert_not_called()


class TestB04RetrievalService(unittest.TestCase):
    def test_preserves_retrieved_memory(self):
        store = Mock()
        expected = make_memory()
        store.get_version.return_value = expected

        service = RetrievalService(store)
        result = service.get_version(version_id=expected.version_id)

        self.assertIs(result, expected)
        store.get_version.assert_called_once_with(expected.version_id)

    def test_not_found_is_preserved(self):
        store = Mock()
        store.get_version.return_value = None

        service = RetrievalService(store)
        result = service.get_version(version_id=uuid4())

        self.assertIsNone(result)

    def test_rejects_non_uuid(self):
        service = RetrievalService(Mock())

        with self.assertRaises(TypeError):
            service.get_version(version_id="not-a-uuid")


class TestB04ContextAssembler(unittest.TestCase):
    def setUp(self):
        self.assembler = ContextAssembler()

    def test_preserves_identity_content_and_provenance(self):
        memory = make_memory("alpha")

        result = self.assembler.assemble(
            memories=[memory],
            max_items=5,
            max_characters=100,
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.context_items), 1)

        item = result.context_items[0]
        self.assertIsInstance(item, ContextItem)
        self.assertEqual(item.atom_id, memory.atom_id)
        self.assertEqual(item.version_id, memory.version_id)
        self.assertEqual(item.content, memory.content)
        self.assertEqual(item.provenance, memory.provenance)

    def test_preserves_input_order(self):
        memories = [make_memory("first"), make_memory("second")]

        result = self.assembler.assemble(
            memories=memories,
            max_items=5,
            max_characters=100,
        )

        self.assertEqual(
            result.included_version_ids,
            tuple(memory.version_id for memory in memories),
        )

    def test_excludes_complete_record_when_character_limit_exceeded(self):
        memories = [make_memory("12345"), make_memory("67890")]

        result = self.assembler.assemble(
            memories=memories,
            max_items=5,
            max_characters=7,
        )

        self.assertEqual(len(result.context_items), 1)
        self.assertEqual(result.context_items[0].content, "12345")
        self.assertEqual(result.total_characters, 5)
        self.assertEqual(
            result.excluded_version_ids,
            (memories[1].version_id,),
        )

    def test_character_limit_counts_content_only(self):
        memory = make_memory("x")

        result = self.assembler.assemble(
            memories=[memory],
            max_items=5,
            max_characters=1,
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.context_items), 1)
        self.assertEqual(result.context_items[0].content, "x")
        self.assertEqual(result.total_characters, 1)

    def test_continues_after_excluding_non_fitting_record(self):
        memories = [
            make_memory("123456"),
            make_memory("ab"),
            make_memory("c"),
        ]

        result = self.assembler.assemble(
            memories=memories,
            max_items=5,
            max_characters=3,
        )

        self.assertEqual(
            result.included_version_ids,
            (memories[1].version_id, memories[2].version_id),
        )
        self.assertEqual(
            result.excluded_version_ids,
            (memories[0].version_id,),
        )
        self.assertEqual(
            tuple(item.content for item in result.context_items),
            ("ab", "c"),
        )
        self.assertEqual(result.total_characters, 3)

    def test_item_limit_is_enforced(self):
        memories = [make_memory("one"), make_memory("two")]

        result = self.assembler.assemble(
            memories=memories,
            max_items=1,
            max_characters=100,
        )

        self.assertEqual(len(result.context_items), 1)
        self.assertEqual(result.excluded_version_ids, (memories[1].version_id,))

    def test_empty_input_returns_empty_success(self):
        result = self.assembler.assemble(
            memories=[],
            max_items=5,
            max_characters=100,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.context_items, ())
        self.assertEqual(result.total_characters, 0)

    def test_rejects_duplicate_versions(self):
        memory = make_memory()

        with self.assertRaises(ValueError):
            self.assembler.assemble(
                memories=[memory, memory],
                max_items=5,
                max_characters=100,
            )

    def test_rejects_negative_limits(self):
        with self.assertRaises(ValueError):
            self.assembler.assemble(
                memories=[],
                max_items=-1,
                max_characters=100,
            )


class TestB04ApplicationEntry(unittest.TestCase):
    def test_coordinates_capture(self):
        store = Mock()
        expected = Mock(spec=CaptureResult)
        store.capture.return_value = expected

        app = DynamicMemoryApplication(store=store)
        result = app.capture(
            request=make_request(),
            source_id="trusted-source",
        )

        self.assertIs(result, expected)
        store.capture.assert_called_once()

    def test_coordinates_context_assembly(self):
        store = Mock()
        app = DynamicMemoryApplication(store=store)
        memory = make_memory()

        result = app.assemble_context(
            memories=[memory],
            max_items=2,
            max_characters=100,
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.context_items), 1)


if __name__ == "__main__":
    unittest.main()