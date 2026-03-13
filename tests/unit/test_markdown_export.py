from __future__ import annotations

from app.export.markdown import render_note_markdown


def test_render_note_markdown_includes_text_math_and_image_links() -> None:
    content_json: dict[str, object] = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Graph Notes"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Relation score: "},
                    {"type": "mathInline", "attrs": {"latex": "x^2+y^2"}},
                ],
            },
            {
                "type": "mathBlock",
                "attrs": {"latex": "\\int_0^1 x dx"},
            },
            {
                "type": "image",
                "attrs": {
                    "src": "/v1/media/asset-1",
                    "assetId": "asset-1",
                    "alt": "diagram",
                    "filename": "asset-1.png",
                },
            },
        ],
    }

    output = render_note_markdown(content_json)
    assert "# Graph Notes" in output
    assert "Relation score: $x^2+y^2$" in output
    assert "$$\\int_0^1 x dx$$" in output
    assert "![diagram](assets/asset-1.png)" in output
