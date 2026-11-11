import sys
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dynamic_memory.contracts import CaptureRequest, calculate_content_hash
from dynamic_memory.persistence import MemoryStore


SCHEMA_PATH = ROOT / "src" / "dynamic_memory" / "schema.sql"


def make_request(content):
    return CaptureRequest(
        content=content,
        knowledge_type="fact",
        epistemic_status="asserted",
        verification_status="unverified",
        source_type="integration-test",
        source_locator="test-case",
    )


class TestB03Persistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_memory.db"

        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(schema)

        self.store = MemoryStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def counts(self):
        with sqlite3.connect(self.db_path) as connection:
            return {
                table: connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                for table in (
                    "atoms",
                    "atom_versions",
                    "provenance",
                    "activity_events",
                )
            }

    def test_01_capture_persists_all_records(self):
        result = self.store.capture(
            make_request("First memory"),
            source_id="source-001",
        )

        counts = self.counts()

        self.assertEqual(counts["atoms"], 1)
        self.assertEqual(counts["atom_versions"], 1)
        self.assertEqual(counts["provenance"], 1)
        self.assertEqual(counts["activity_events"], 1)
        self.assertEqual(result.version_no, 1)
        self.assertEqual(
            result.content_hash,
            calculate_content_hash("First memory"),
        )
        self.assertEqual(len(result.provenance_ids), 1)

    def test_02_revision_appends_version_two(self):
        first = self.store.capture(
            make_request("Original assertion"),
            source_id="source-001",
        )

        second = self.store.revise(
            first.atom_id,
            make_request("Revised assertion"),
            source_id="source-002",
        )

        self.assertEqual(second.atom_id, first.atom_id)
        self.assertEqual(second.version_no, 2)
        self.assertNotEqual(second.version_id, first.version_id)

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT version_no, supersedes_version_id
                FROM atom_versions
                WHERE version_id = ?
                """,
                (str(second.version_id),),
            ).fetchone()

        self.assertEqual(row[0], 2)
        self.assertEqual(row[1], str(first.version_id))

        counts = self.counts()
        self.assertEqual(counts["atoms"], 1)
        self.assertEqual(counts["atom_versions"], 2)
        self.assertEqual(counts["provenance"], 2)
        self.assertEqual(counts["activity_events"], 2)

    def test_03_retrieval_reconstructs_contract_and_hash(self):
        result = self.store.capture(
            make_request("Unicode memory — 🦅"),
            source_id="source-003",
        )

        retrieved = self.store.get_version(result.version_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.atom_id, result.atom_id)
        self.assertEqual(retrieved.version_id, result.version_id)
        self.assertEqual(retrieved.content, "Unicode memory — 🦅")
        self.assertEqual(
            retrieved.content_hash,
            calculate_content_hash(retrieved.content),
        )
        self.assertEqual(len(retrieved.provenance), 1)
        self.assertEqual(
            retrieved.provenance[0].source_id,
            "source-003",
        )

    def test_04_original_version_survives_revision(self):
        first = self.store.capture(
            make_request("Original assertion"),
            source_id="source-001",
        )

        self.store.revise(
            first.atom_id,
            make_request("New assertion"),
            source_id="source-002",
        )

        original = self.store.get_version(first.version_id)

        self.assertEqual(original.content, "Original assertion")
        self.assertEqual(original.version_no, 1)

    def test_05_foreign_keys_enabled_on_store_connection(self):
        connection = self.store._connect()
        try:
            enabled = connection.execute(
                "PRAGMA foreign_keys"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(enabled, 1)

    def test_06_immutable_version_update_rejected(self):
        result = self.store.capture(
            make_request("Immutable assertion"),
            source_id="source-001",
        )

        connection = self.store._connect()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    UPDATE atom_versions
                    SET content = ?
                    WHERE version_id = ?
                    """,
                    ("Changed content", str(result.version_id)),
                )
        finally:
            connection.close()

    def test_07_capture_failure_rolls_back_everything(self):
        before = self.counts()

        with patch.object(
            MemoryStore,
            "_insert_provenance",
            side_effect=RuntimeError("Forced provenance failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Forced provenance failure",
            ):
                self.store.capture(
                    make_request("Must roll back"),
                    source_id="source-failure",
                )

        self.assertEqual(self.counts(), before)

    def test_08_revision_failure_rolls_back_everything(self):
        first = self.store.capture(
            make_request("Stable original"),
            source_id="source-001",
        )
        before = self.counts()

        with patch.object(
            MemoryStore,
            "_insert_provenance",
            side_effect=RuntimeError("Forced revision failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Forced revision failure",
            ):
                self.store.revise(
                    first.atom_id,
                    make_request("Must not persist"),
                    source_id="source-failure",
                )

        self.assertEqual(self.counts(), before)

        original = self.store.get_version(first.version_id)
        self.assertEqual(original.content, "Stable original")

    def test_09_tampered_content_fails_hash_verification(self):
        result = self.store.capture(
            make_request("Original content"),
            source_id="source-001",
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DROP TRIGGER prevent_atom_version_update"
            )
            connection.execute(
                """
                UPDATE atom_versions
                SET content = ?
                WHERE version_id = ?
                """,
                ("Tampered content", str(result.version_id)),
            )

        with self.assertRaisesRegex(ValueError, "Content hash mismatch"):
            self.store.get_version(result.version_id)

    def test_10_missing_version_returns_none(self):
        from uuid import uuid4

        self.assertIsNone(self.store.get_version(uuid4()))


if __name__ == "__main__":
    unittest.main(verbosity=2)