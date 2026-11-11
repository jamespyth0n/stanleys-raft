"""Deterministic tests for the Ollama HTTP adapter."""

import io
import json
import unittest

from urllib.error import HTTPError, URLError

from dynamic_memory.application.ollama_adapter import OllamaModelAdapter


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._body


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))

        if self.error is not None:
            raise self.error

        return self.response


def ollama_body(
    content="Hello from Ollama.",
    model="qwen2.5:14b",
):
    return json.dumps({
        "model": model,
        "message": {
            "role": "assistant",
            "content": content,
        },
        "done": True,
    }).encode("utf-8")


class TestOllamaModelAdapter(unittest.TestCase):

    def test_successful_response(self):
        opener = FakeOpener(
            response=FakeResponse(ollama_body())
        )
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Say hello.")

        self.assertTrue(result.success)
        self.assertEqual(result.response_text, "Hello from Ollama.")
        self.assertEqual(result.model_name, "qwen2.5:14b")
        self.assertIsNone(result.error_type)

    def test_request_uses_chat_endpoint_and_non_streaming(self):
        opener = FakeOpener(
            response=FakeResponse(ollama_body())
        )
        adapter = OllamaModelAdapter(
            model_name="test-model",
            base_url="http://localhost:11434/",
            timeout=12.0,
            opener=opener,
        )

        adapter.generate(prompt="Test prompt.")

        request, timeout = opener.calls[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(
            request.full_url,
            "http://localhost:11434/api/chat",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(
            payload["messages"],
            [{"role": "user", "content": "Test prompt."}],
        )
        self.assertFalse(payload["stream"])
        self.assertEqual(timeout, 12.0)

    def test_timeout_is_explicit(self):
        opener = FakeOpener(error=TimeoutError("timed out"))
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "timeout")
        self.assertEqual(result.response_text, "")

    def test_connection_failure_is_explicit(self):
        opener = FakeOpener(
            error=URLError("connection refused")
        )
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "connection_error")

    def test_http_failure_is_explicit(self):
        error = HTTPError(
            "http://localhost:11434/api/chat",
            503,
            "Service unavailable",
            hdrs=None,
            fp=io.BytesIO(b""),
        )
        opener = FakeOpener(error=error)
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "http_error")
        self.assertIn("503", result.error_message)

    def test_malformed_json_is_rejected(self):
        opener = FakeOpener(
            response=FakeResponse(b"{not-json")
        )
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "malformed_json")

    def test_missing_message_object_is_rejected(self):
        opener = FakeOpener(
            response=FakeResponse(
                json.dumps({"model": "test-model"}).encode("utf-8")
            )
        )
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "invalid_response")

    def test_missing_assistant_content_is_rejected(self):
        body = json.dumps({
            "model": "test-model",
            "message": {"role": "assistant"},
        }).encode("utf-8")
        opener = FakeOpener(response=FakeResponse(body))
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "invalid_response")

    def test_requested_model_overrides_default(self):
        opener = FakeOpener(
            response=FakeResponse(
                ollama_body(model="requested-model")
            )
        )
        adapter = OllamaModelAdapter(
            model_name="default-model",
            opener=opener,
        )

        result = adapter.generate(
            prompt="Test.",
            model_name="requested-model",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.model_name, "requested-model")

    def test_empty_prompt_is_rejected_without_http_call(self):
        opener = FakeOpener()
        adapter = OllamaModelAdapter(opener=opener)

        result = adapter.generate(prompt=" ")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "invalid_request")
        self.assertEqual(opener.calls, [])

    def test_provider_reported_model_not_found(self):
        body = json.dumps({
            "error": "model 'qwen2.5:14b' not found"
        }).encode("utf-8")
        adapter = OllamaModelAdapter(
            opener=FakeOpener(response=FakeResponse(body))
        )

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "provider_error")
        self.assertIn("not found", result.error_message)
        self.assertEqual(result.response_text, "")

    def test_generic_provider_reported_error(self):
        body = json.dumps({
            "error": "model loading failed"
        }).encode("utf-8")
        adapter = OllamaModelAdapter(
            opener=FakeOpener(response=FakeResponse(body))
        )

        result = adapter.generate(prompt="Test.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "provider_error")
        self.assertIn("model loading failed", result.error_message)

    def test_malformed_provider_error_field_is_rejected(self):
        for invalid_error in ("", "   ", 123, None, {"detail": "failed"}):
            with self.subTest(error=invalid_error):
                body = json.dumps({
                    "error": invalid_error
                }).encode("utf-8")
                adapter = OllamaModelAdapter(
                    opener=FakeOpener(response=FakeResponse(body))
                )

                result = adapter.generate(prompt="Test.")

                self.assertFalse(result.success)
                self.assertEqual(result.error_type, "invalid_response")
                self.assertEqual(result.response_text, "")

if __name__ == "__main__":
    unittest.main()