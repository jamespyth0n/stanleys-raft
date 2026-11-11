"""Application boundary for B03 capture operations."""

from dynamic_memory.contracts import CaptureRequest, CaptureResult
from dynamic_memory.persistence import MemoryStore


class CaptureService:
    def __init__(self, store: MemoryStore):
        self._store = store

    def capture(
        self,
        *,
        request: CaptureRequest,
        source_id: str,
    ) -> CaptureResult:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Trusted source_id must be a non-empty string.")

        if not isinstance(request, CaptureRequest):
            raise TypeError("request must be a CaptureRequest.")

        if (
            not isinstance(request.source_type, str)
            or not request.source_type.strip()
        ):
            raise ValueError(
                "Trusted source_type must be a non-empty string."
            )

        return self._store.capture(request, source_id=source_id)