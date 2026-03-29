from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class EntityExtractionMetrics:
    dictionary_hits: int = 0
    spacy_hits: int = 0
    regex_hits: int = 0
    merged_mentions: int = 0


class EntityCandidateExtractor(Protocol):
    layer_name: str

    def extract(
        self,
        *,
        block_text: str,
        dictionary_terms: list[str],
        seed_terms: list[str],
        model_handle: object | None,
    ) -> Sequence[object]:
        ...
