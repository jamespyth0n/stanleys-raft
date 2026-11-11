"""Ollama HTTP implementation of the provider-neutral model adapter."""

import json
import socket
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .results import ModelResult


class OllamaModelAdapter:
    """Generate model responses through Ollama's local HTTP API."""

    def __init__(
        self,
        *,
        model_name: str = "qwen2.5:14b",
        base_url: str = "http://localhost:11434",
        timeout: float = 30.0,
        opener: Optional[Callable] = None,
    ):
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string.")

        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty string.")

        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        self._model_name = model_name.strip()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._opener = opener or urlopen

    def _failure(
        self,
        *,
        model_name: str,
        error_type: str,
        error_message: str,
    ) -> ModelResult:
        return ModelResult(
            success=False,
            response_text="",
            model_name=model_name,
            error_type=error_type,
            error_message=error_message,
        )

    def generate(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
    ) -> ModelResult:
        selected_model = model_name or self._model_name

        if not isinstance(prompt, str) or not prompt.strip():
            return self._failure(
                model_name=selected_model,
                error_type="invalid_request",
                error_message="prompt must be a non-empty string.",
            )

        if not isinstance(selected_model, str) or not selected_model.strip():
            return self._failure(
                model_name=self._model_name,
                error_type="invalid_request",
                error_message="model_name must be a non-empty string.",
            )

        selected_model = selected_model.strip()

        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        }

        request = Request(
            url=f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._opener(
                request,
                timeout=self._timeout,
            ) as response:
                raw_body = response.read()

        except HTTPError as exc:
            return self._failure(
                model_name=selected_model,
                error_type="http_error",
                error_message=f"Ollama returned HTTP {exc.code}.",
            )

        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                return self._failure(
                    model_name=selected_model,
                    error_type="timeout",
                    error_message="Ollama request timed out.",
                )

            return self._failure(
                model_name=selected_model,
                error_type="connection_error",
                error_message=f"Unable to connect to Ollama: {exc.reason}",
            )

        except (TimeoutError, socket.timeout):
            return self._failure(
                model_name=selected_model,
                error_type="timeout",
                error_message="Ollama request timed out.",
            )

        except OSError as exc:
            return self._failure(
                model_name=selected_model,
                error_type="connection_error",
                error_message=f"Ollama connection failed: {exc}",
            )

        try:
            decoded = raw_body.decode("utf-8")
            data = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._failure(
                model_name=selected_model,
                error_type="malformed_json",
                error_message="Ollama returned an invalid JSON response.",
            )

        if not isinstance(data, dict):
            return self._failure(
                model_name=selected_model,
                error_type="invalid_response",
                error_message="Ollama response must be a JSON object.",
            )

        if "error" in data:
            provider_error = data["error"]

            if (
                not isinstance(provider_error, str)
                or not provider_error.strip()
            ):
                return self._failure(
                    model_name=selected_model,
                    error_type="invalid_response",
                    error_message=(
                        "Ollama returned an invalid provider error field."
                    ),
                )

            return self._failure(
                model_name=selected_model,
                error_type="provider_error",
                error_message=f"Ollama reported an error: {provider_error}",
            )

        message = data.get("message")

        if not isinstance(message, dict):
            return self._failure(
                model_name=selected_model,
                error_type="invalid_response",
                error_message="Ollama response is missing its message object.",
            )

        content = message.get("content")

        if not isinstance(content, str):
            return self._failure(
                model_name=selected_model,
                error_type="invalid_response",
                error_message="Ollama response is missing assistant content.",
            )

        returned_model = data.get("model")
        if not isinstance(returned_model, str) or not returned_model.strip():
            returned_model = selected_model

        return ModelResult(
            success=True,
            response_text=content,
            model_name=returned_model,
        )