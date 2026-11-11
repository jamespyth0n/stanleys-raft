import unittest
from uuid import UUID, uuid1, uuid4

from dynamic_memory.contracts import Contract


class UUIDProbe(Contract):
    atom_id: UUID
    version_ids: list[UUID]


class TestUUIDv4ContractEnforcement(unittest.TestCase):

    def test_accepts_uuid4_scalar(self):
        result = UUIDProbe(atom_id=uuid4(), version_ids=[])
        self.assertEqual(result.atom_id.version, 4)

    def test_rejects_uuid1_scalar(self):
        with self.assertRaises(ValueError):
            UUIDProbe(atom_id=uuid1(), version_ids=[])

    def test_accepts_uuid4_list(self):
        result = UUIDProbe(atom_id=uuid4(), version_ids=[uuid4()])
        self.assertEqual(result.version_ids[0].version, 4)

    def test_rejects_uuid1_in_list(self):
        with self.assertRaises(ValueError):
            UUIDProbe(atom_id=uuid4(), version_ids=[uuid1()])


if __name__ == "__main__":
    unittest.main()