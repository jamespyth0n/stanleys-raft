"""Gate 3 provider-neutral model adapter tests."""

import unittest

from dynamic_memory.application.model_adapter import MockModelAdapter
from dynamic_memory.application.results import ModelResult


class TestModelResult(unittest.TestCase):
    def test_result_is_immutable(self):
        result = ModelResult(
            success=True,
            response_text="hello",
            model_name="test-model",
        )

        with self.assertRaises(AttributeError):
            result.success = False


class TestMockModelAdapter(unittest.TestCase):
    def test_returns_queued_result(self):
        expected = ModelResult(
            success=True,
            response_text="model output",
            model_name="test-model",
        )
        adapter = MockModelAdapter([expected])

        result = adapter.generate(prompt="test prompt")

        self.assertIs(result, expected)

    def test_records_generation_arguments(self):
        adapter = MockModelAdapter([
            ModelResult(
                success=True,
                response_text="output",
                model_name="test-model",
            )
        ])

        adapter.generate(
            prompt="test prompt",
            model_name="test-model",
        )

        self.assertEqual(
            adapter.calls,
            [("test prompt", "test-model")],
        )

    def test_returns_explicit_failure_when_responses_exhausted(self):
        adapter = MockModelAdapter()

        result = adapter.generate(prompt="test prompt")

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_type,
            "mock_response_exhausted",
        )
        self.assertEqual(result.response_text, "")

    def test_responses_are_consumed_in_order(self):
        first = ModelResult(True, "first", "model")
        second = ModelResult(True, "second", "model")
        adapter = MockModelAdapter([first, second])

        self.assertIs(adapter.generate(prompt="one"), first)
        self.assertIs(adapter.generate(prompt="two"), second)


if __name__ == "__main__":
    unittest.main()