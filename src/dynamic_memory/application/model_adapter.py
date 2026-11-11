"""Provider-neutral model adapter boundary and deterministic mock."""

from collections import deque
from typing import Deque, Protocol, Sequence

from .results import ModelResult


class ModelAdapter(Protocol):
    """Provider-independent interface for model generation."""

    def generate(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
    ) -> ModelResult:
        ...


class MockModelAdapter:
    """Deterministic adapter for isolated application tests."""

    def __init__(self, results: Sequence[ModelResult] = ()):
        self._results: Deque[ModelResult] = deque(results)
        self.calls: list[tuple[str, str | None]] = []

    def generate(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
    ) -> ModelResult:
        self.calls.append((prompt, model_name))

        if not self._results:
            return ModelResult(
                success=False,
                response_text="",
                model_name=model_name or "mock",
                error_type="mock_response_exhausted",
                error_message="No queued mock response is available.",
            )

        return self._results.popleft()