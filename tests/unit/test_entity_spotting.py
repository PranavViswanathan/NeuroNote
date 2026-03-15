from __future__ import annotations

from app.nlp.spotting import extract_entities_with_mentions
from app.nlp.types import BlockTextInput


def test_spotter_uses_dictionary_terms_with_block_offsets() -> None:
    entities, mentions = extract_entities_with_mentions(
        blocks=[
            BlockTextInput(
                block_index=0,
                content_text="Machine Learning improves graph reasoning.",
            )
        ],
        dictionary_terms=["machine learning", "graph reasoning"],
    )

    assert [entity.text for entity in entities] == ["graph reasoning", "Machine Learning"]
    assert len(mentions) == 2
    assert mentions[0].block_index == 0
    assert mentions[0].mention_text == "Machine Learning"
    assert mentions[0].start_offset == 0
    assert mentions[0].end_offset == 16
    assert mentions[1].mention_text == "graph reasoning"


def test_spotter_falls_back_to_title_case_and_acronyms() -> None:
    entities, mentions = extract_entities_with_mentions(
        blocks=[
            BlockTextInput(
                block_index=1,
                content_text="Entity Resolution supports ML systems.",
            )
        ],
    )

    assert {entity.text for entity in entities} == {"Entity Resolution", "ML"}
    assert all(mention.block_index == 1 for mention in mentions)


def test_spotter_dedupes_and_sorts_mentions_deterministically() -> None:
    entities, mentions = extract_entities_with_mentions(
        blocks=[
            BlockTextInput(block_index=0, content_text="ML supports ML workflows."),
            BlockTextInput(block_index=1, content_text="Machine Learning supports ML."),
        ],
        dictionary_terms=["machine learning", "ml"],
    )

    assert any(entity.text == "ML" for entity in entities)
    assert len(mentions) == 4
    assert [(item.block_index, item.start_offset) for item in mentions] == [
        (0, 0),
        (0, 12),
        (1, 0),
        (1, 26),
    ]
