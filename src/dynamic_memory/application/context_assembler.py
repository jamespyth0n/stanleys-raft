"""Deterministic, bounded context assembly."""

from typing import Sequence

from dynamic_memory.contracts import ContextItem, RetrievedMemory
from .results import ContextAssemblyResult


class ContextAssembler:
    """Build ContextItems in input order without ranking or truncation.

    Records that exceed a limit are excluded as complete records.
    The assembler never truncates individual memory content.
    """

    def assemble(
        self,
        *,
        memories: Sequence[RetrievedMemory],
        max_items: int,
        max_characters: int,
    ) -> ContextAssemblyResult:
        if isinstance(max_items, bool) or not isinstance(max_items, int):
            raise TypeError("max_items must be an integer.")

        if isinstance(max_characters, bool) or not isinstance(max_characters, int):
            raise TypeError("max_characters must be an integer.")

        if max_items < 0 or max_characters < 0:
            raise ValueError("Context limits cannot be negative.")

        if not isinstance(memories, (list, tuple)):
            raise TypeError("memories must be a list or tuple.")

        seen = set()
        for memory in memories:
            if not isinstance(memory, RetrievedMemory):
                raise TypeError("Every memory must be a RetrievedMemory.")

            if memory.version_id in seen:
                raise ValueError(
                    f"Duplicate version_id supplied: {memory.version_id}"
                )
            seen.add(memory.version_id)

        included = []
        excluded = []
        included_ids = []
        excluded_ids = []
        total_characters = 0

        for memory in memories:
            content_length = len(memory.content)

            fits_item_limit = len(included) < max_items
            fits_character_limit = (
                total_characters + content_length <= max_characters
            )

            if fits_item_limit and fits_character_limit:
                item = ContextItem(
                    atom_id=memory.atom_id,
                    version_id=memory.version_id,
                    content=memory.content,
                    provenance=memory.provenance,
                )
                included.append(item)
                included_ids.append(memory.version_id)
                total_characters += content_length
            else:
                excluded_ids.append(memory.version_id)

        return ContextAssemblyResult(
            success=True,
            context_items=tuple(included),
            included_version_ids=tuple(included_ids),
            excluded_version_ids=tuple(excluded_ids),
            total_characters=total_characters,
        )