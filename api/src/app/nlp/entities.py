from __future__ import annotations

from app.nlp.spotting import extract_entities_with_mentions
from app.nlp.types import BlockTextInput
from app.nlp.types import ExtractedEntity

def extract_entities(text: str) -> list[ExtractedEntity]:
    entities, _mentions = extract_entities_with_mentions(
        blocks=[BlockTextInput(block_index=0, content_text=text)],
        dictionary_terms=[],
    )
    return entities
