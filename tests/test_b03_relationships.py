import sqlite3
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from dynamic_memory.contracts import CaptureRequest, RelationshipRecord
from dynamic_memory.persistence import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src" / "dynamic_memory" / "schema.sql"


def make_request(content):
    return CaptureRequest(
        content=content,
        knowledge_type="fact",
        epistemic_status="asserted",
        verification_status="unverified",
        source_type="relationship-test",
        source_locator="f02",
    )


class TestB03Relationships(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "relationships.db"

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection = sqlite3.connect(str(self.db_path))
        try:
            connection.executescript(schema)
            connection.commit()
        finally:
            connection.close()

        self.store = MemoryStore(self.db_path)

    def tearDown(self):
        self.store = None
        self.temp_dir.cleanup()

    def capture_version(self, content):
        result = self.store.capture(
            make_request(content),
            source_id="f02-test-source",
        )
        return result.version_id

    def relation_count(self):
        connection = sqlite3.connect(str(self.db_path))
        try:
            return connection.execute(
                "SELECT COUNT(*) FROM atom_version_relations"
            ).fetchone()[0]
        finally:
            connection.close()

    def test_01_create_disputes_relationship(self):
        source = self.capture_version("Source assertion")
        target = self.capture_version("Target assertion")

        result = self.store.add_relationship(source, target)

        self.assertIsInstance(result, RelationshipRecord)
        self.assertEqual(result.from_version_id, source)
        self.assertEqual(result.to_version_id, target)
        self.assertEqual(result.relation_type, "disputes")
        self.assertEqual(result.relation_id.version, 4)
        self.assertIsNotNone(result.created_at.utcoffset())
        self.assertEqual(self.relation_count(), 1)

    def test_02_retrieve_outgoing_relationship(self):
        source = self.capture_version("Source assertion")
        target = self.capture_version("Target assertion")

        created = self.store.add_relationship(source, target)
        results = self.store.get_relationships(source)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], created)

    def test_03_retrieve_incoming_relationship(self):
        source = self.capture_version("Source assertion")
        target = self.capture_version("Target assertion")

        created = self.store.add_relationship(source, target)
        results = self.store.get_relationships(target)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], created)

    def test_04_unrelated_version_returns_empty_list(self):
        source = self.capture_version("Source assertion")
        target = self.capture_version("Target assertion")
        unrelated = self.capture_version("Unrelated assertion")

        self.store.add_relationship(source, target)

        self.assertEqual(
            self.store.get_relationships(unrelated),
            [],
        )

    def test_05_missing_source_version_rejected(self):
        target = self.capture_version("Target assertion")

        with self.assertRaisesRegex(ValueError, "Source version"):
            self.store.add_relationship(uuid4(), target)

        self.assertEqual(self.relation_count(), 0)

    def test_06_missing_target_version_rejected(self):
        source = self.capture_version("Source assertion")

        with self.assertRaisesRegex(ValueError, "Target version"):
            self.store.add_relationship(source, uuid4())

        self.assertEqual(self.relation_count(), 0)

    def test_07_self_relationship_rejected(self):
        version = self.capture_version("Single assertion")

        with self.assertRaisesRegex(ValueError, "itself"):
            self.store.add_relationship(version, version)

        self.assertEqual(self.relation_count(), 0)

    def test_08_no_partial_record_after_insert_failure(self):
        source = self.capture_version("Source assertion")
        target = self.capture_version("Target assertion")

        connection = sqlite3.connect(str(self.db_path))
        try:
            connection.execute(
                """
                CREATE TRIGGER reject_relationship_insert
                BEFORE INSERT ON atom_version_relations
                BEGIN
                    SELECT RAISE(ABORT, 'forced relationship failure');
                END
                """
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_relationship(source, target)

        self.assertEqual(self.relation_count(), 0)

    def test_09_foreign_keys_enabled_on_relationship_connection(self):
        connection = self.store._connect()
        try:
            enabled = connection.execute(
                "PRAGMA foreign_keys"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(enabled, 1)


if __name__ == "__main__":
    unittest.main()