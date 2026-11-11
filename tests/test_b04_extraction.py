"""Gate 3 extraction acceptance tests."""

import json
import unittest
from datetime import datetime, timezone

from dynamic_memory.application.extraction import (
    ExtractionCandidate,
    ExtractionService,
)
from dynamic_memory.application.model_adapter import MockModelAdapter
from dynamic_memory.application.results import ModelResult
from dynamic_memory.contracts import EpistemicStatus, KnowledgeType


def response(candidates):
    return json.dumps({"candidates": candidates})


def candidate(
    content="The sky is blue.",
    knowledge_type="fact",
    epistemic_status="observed",
    valid_from=None,
    valid_until=None,
):
    return {
        "content": content,
        "knowledge_type": knowledge_type,
        "epistemic_status": epistemic_status,
        "valid_from": valid_from,
        "valid_until": valid_until,
    }


def service_for(text):
    adapter = MockModelAdapter([
        ModelResult(True, text, "test-model")
    ])
    return ExtractionService(adapter=adapter), adapter


class TestExtractionCandidate(unittest.TestCase):

    def test_candidate_is_immutable(self):
        item = ExtractionCandidate.model_validate(candidate())

        with self.assertRaises(Exception):
            item.content = "changed"

    def test_datetime_normalizes_to_utc(self):
        item = ExtractionCandidate.model_validate(candidate(
            valid_from="2026-01-01T05:00:00+05:00"
        ))

        self.assertEqual(
            item.valid_from,
            datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        )

    def test_naive_datetime_is_rejected(self):
        with self.assertRaises(ValueError):
            ExtractionCandidate.model_validate(candidate(
                valid_from="2026-01-01T05:00:00"
            ))


class TestExtractionAcceptance(unittest.TestCase):

    def test_at01_valid_single_candidate(self):
        service, _ = service_for(response([candidate()]))

        result = service.extract(source_content="Source.")

        self.assertTrue(result.success)
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].content, "The sky is blue.")
        self.assertEqual(result.candidates[0].knowledge_type, KnowledgeType.FACT)
        self.assertEqual(
            result.candidates[0].epistemic_status,
            EpistemicStatus.OBSERVED,
        )

    def test_at02_multiple_candidates_preserve_order(self):
        service, _ = service_for(response([
            candidate(content="First."),
            candidate(content="Second."),
        ]))

        result = service.extract(source_content="Source.")

        self.assertTrue(result.success)
        self.assertEqual(
            [item.content for item in result.candidates],
            ["First.", "Second."],
        )

    def test_at03_empty_candidate_list_is_valid(self):
        service, _ = service_for(response([]))

        result = service.extract(source_content="Source.")

        self.assertTrue(result.success)
        self.assertEqual(result.candidates, ())

    def test_at04_malformed_json_fails(self):
        service, _ = service_for("{not-json")

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "malformed_extraction_output")
        self.assertEqual(result.candidates, ())

    def test_at05_missing_required_field_fails(self):
        invalid = candidate()
        del invalid["epistemic_status"]
        service, _ = service_for(response([invalid]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at06_unsupported_field_fails(self):
        invalid = candidate()
        invalid["unexpected"] = "not allowed"
        service, _ = service_for(response([invalid]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at07_invalid_knowledge_type_fails(self):
        service, _ = service_for(response([
            candidate(knowledge_type="unsupported_type")
        ]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at08_invalid_epistemic_status_fails(self):
        service, _ = service_for(response([
            candidate(epistemic_status="verified")
        ]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at09_naive_datetime_fails(self):
        service, _ = service_for(response([
            candidate(valid_from="2026-01-01T00:00:00")
        ]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at10_invalid_temporal_interval_fails(self):
        service, _ = service_for(response([
            candidate(
                valid_from="2026-02-01T00:00:00Z",
                valid_until="2026-01-01T00:00:00Z",
            )
        ]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at11_provider_failure_is_explicit(self):
        adapter = MockModelAdapter([
            ModelResult(
                False,
                "",
                "test-model",
                error_type="timeout",
                error_message="Timed out.",
            )
        ])
        service = ExtractionService(adapter=adapter)

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "timeout")
        self.assertIn("Timed out.", result.error_message)

    def test_at12_provenance_and_verification_fields_are_rejected(self):
        invalid = candidate()
        invalid["source_id"] = "model-supplied"
        invalid["verification_status"] = "verified"
        service, _ = service_for(response([invalid]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_at13_extraction_has_no_persistence_dependency(self):
        service, adapter = service_for(response([candidate()]))

        result = service.extract(source_content="Source.")

        self.assertTrue(result.success)
        self.assertEqual(len(adapter.calls), 1)
        self.assertFalse(hasattr(service, "_store"))

    def test_invalid_candidate_rejects_entire_batch(self):
        invalid = candidate(knowledge_type="not-a-real-type")
        service, _ = service_for(response([
            candidate(content="Valid first candidate."),
            invalid,
        ]))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.candidates, ())

    def test_blank_source_is_rejected_without_model_call(self):
        adapter = MockModelAdapter()
        service = ExtractionService(adapter=adapter)

        result = service.extract(source_content=" ")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "validation_failure")
        self.assertEqual(adapter.calls, [])

    def test_root_extra_field_is_rejected(self):
        payload = {
            "candidates": [candidate()],
            "source_id": "untrusted",
        }
        service, _ = service_for(json.dumps(payload))

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "contract_validation_failure")

    def test_http_provider_failure_remains_provider_failure(self):
        adapter = MockModelAdapter([
            ModelResult(
                False,
                "",
                "test-model",
                error_type="http_error",
                error_message="HTTP 503.",
            )
        ])
        service = ExtractionService(adapter=adapter)

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "provider_failure")

    def test_malformed_provider_response_is_distinct(self):
        adapter = MockModelAdapter([
            ModelResult(True, None, "test-model")
        ])
        service = ExtractionService(adapter=adapter)

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_type,
            "malformed_provider_response",
        )

    def test_invalid_adapter_result_is_unexpected_internal_failure(self):
        class InvalidAdapter:
            def generate(self, *, prompt, model_name=None):
                return object()

        service = ExtractionService(adapter=InvalidAdapter())

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_type,
            "unexpected_internal_failure",
        )

    def test_unexpected_adapter_exception_is_classified(self):
        class RaisingAdapter:
            def generate(self, *, prompt, model_name=None):
                raise RuntimeError("unexpected test failure")

        service = ExtractionService(adapter=RaisingAdapter())

        result = service.extract(source_content="Source.")

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_type,
            "unexpected_internal_failure",
        )
        self.assertIn("RuntimeError", result.error_message)
    def test_provider_reported_error_maps_to_provider_failure(self):
        adapter = MockModelAdapter([
            ModelResult(
                False,
                "",
                "test-model",
                error_type="provider_error",
                error_message="Ollama reported model not found.",
            )
        ])
        service = ExtractionService(adapter=adapter)

        result = service.extract(source_content="Source content.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "provider_failure")
        self.assertEqual(result.candidates, ())

if __name__ == "__main__":
    unittest.main()