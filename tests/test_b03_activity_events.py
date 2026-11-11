import json
import sqlite3
import tempfile
import unittest

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from dynamic_memory.contracts import (
    ActivityEvent,
    CaptureRequest,
    EpistemicStatus,
    KnowledgeType,
)
from dynamic_memory.persistence import MemoryStore


class TestB03ActivityEvents(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "activity_test.db"

        schema_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "dynamic_memory"
            / "schema.sql"
        )

        connection = sqlite3.connect(self.db_path)
        try:
            connection.executescript(
                schema_path.read_text(encoding="utf-8")
            )
            connection.commit()
        finally:
            connection.close()

        self.store = MemoryStore(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_request(self, content):
        return CaptureRequest(
            content=content,
            knowledge_type=KnowledgeType.FACT,
            epistemic_status=EpistemicStatus.ASSERTED,
            source_type="unit_test",
        )

    def capture_memory(self, content="Activity test memory"):
        return self.store.capture(
            self.make_request(content),
            source_id="activity-test",
        )

    def insert_raw_event(self, details_json):
        event_id = uuid4()
        occurred_at = datetime.now(timezone.utc).isoformat()

        connection = self.store._connect()
        try:
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
                VALUES (?, ?, ?, NULL, NULL, ?)
                """,
                (
                    str(event_id),
                    "test_event",
                    occurred_at,
                    details_json,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        return event_id

    def test_01_retrieve_capture_event(self):
        result = self.capture_memory()

        events = self.store.get_activity_events(
            version_id=result.version_id
        )

        self.assertEqual(len(events), 1)
        event = events[0]

        self.assertIsInstance(event, ActivityEvent)
        self.assertEqual(event.event_type, "memory_captured")
        self.assertEqual(event.atom_id, result.atom_id)
        self.assertEqual(event.version_id, result.version_id)
        self.assertEqual(event.details["version_no"], 1)
        self.assertEqual(event.details["source_type"], "unit_test")
        self.assertEqual(event.event_id.version, 4)
        self.assertIsNotNone(event.occurred_at.tzinfo)

    def test_02_retrieve_revision_event_and_details(self):
        original = self.capture_memory("Original content")

        revised = self.store.revise(
            original.atom_id,
            self.make_request("Revised content"),
            source_id="activity-test",
        )

        events = self.store.get_activity_events(
            version_id=revised.version_id
        )

        self.assertEqual(len(events), 1)
        event = events[0]

        self.assertEqual(event.event_type, "memory_revised")
        self.assertEqual(
            event.details["supersedes_version_id"],
            str(original.version_id),
        )
        self.assertEqual(event.details["version_no"], 2)

    def test_03_filter_by_atom(self):
        first = self.capture_memory("First atom")
        second = self.capture_memory("Second atom")

        events = self.store.get_activity_events(atom_id=first.atom_id)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].atom_id, first.atom_id)
        self.assertNotEqual(events[0].atom_id, second.atom_id)

    def test_04_filter_by_version(self):
        result = self.capture_memory()

        events = self.store.get_activity_events(
            version_id=result.version_id
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].version_id, result.version_id)

    def test_05_combined_filters(self):
        first = self.capture_memory("First memory")
        self.capture_memory("Second memory")

        events = self.store.get_activity_events(
            atom_id=first.atom_id,
            version_id=first.version_id,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].atom_id, first.atom_id)
        self.assertEqual(events[0].version_id, first.version_id)

    def test_06_all_events_have_deterministic_order(self):
        self.capture_memory("First")
        self.capture_memory("Second")
        self.capture_memory("Third")

        events = self.store.get_activity_events()

        keys = [
            (event.occurred_at, str(event.event_id))
            for event in events
        ]

        self.assertEqual(keys, sorted(keys))

    def test_07_no_matching_events_returns_empty_list(self):
        events = self.store.get_activity_events(atom_id=uuid4())

        self.assertEqual(events, [])

    def test_08_sql_null_details_preserved_as_none(self):
        self.insert_raw_event(None)

        events = self.store.get_activity_events()

        event = next(item for item in events if item.event_type == "test_event")
        self.assertIsNone(event.details)

    def test_09_malformed_json_rejected(self):
        event_id = self.insert_raw_event("{not valid json")

        with self.assertRaisesRegex(ValueError, str(event_id)):
            self.store.get_activity_events()

    def test_10_non_object_json_rejected(self):
        event_id = self.insert_raw_event('["not", "an", "object"]')

        with self.assertRaisesRegex(ValueError, str(event_id)):
            self.store.get_activity_events()

    def test_11_json_object_reconstructed(self):
        expected = {"alpha": 1, "nested": {"beta": True}}
        self.insert_raw_event(
            json.dumps(expected, separators=(",", ":"))
        )

        events = self.store.get_activity_events()
        event = next(item for item in events if item.event_type == "test_event")

        self.assertEqual(event.details, expected)


if __name__ == "__main__":
    unittest.main()