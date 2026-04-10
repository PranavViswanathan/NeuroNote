from __future__ import annotations

import pytest

from app.services.note_import_service import NoteImportService, UnsupportedFileTypeError


class TestExtractPlainText:
    def test_extracts_text_from_paragraph_nodes(self) -> None:
        content_json = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]},
            ],
        }
        result = NoteImportService.extract_plain_text(content_json)
        assert result == "Hello world"

    def test_joins_multiple_paragraphs_with_space(self) -> None:
        content_json = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "First"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Second"}]},
            ],
        }
        result = NoteImportService.extract_plain_text(content_json)
        assert "First" in result
        assert "Second" in result

    def test_returns_fallback_for_empty_doc(self) -> None:
        content_json = {"type": "doc", "content": []}
        result = NoteImportService.extract_plain_text(content_json)
        assert result == " "

    def test_ignores_non_text_child_nodes(self) -> None:
        content_json = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "image", "attrs": {}}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Real text"}]},
            ],
        }
        result = NoteImportService.extract_plain_text(content_json)
        assert result == "Real text"


class TestParseContent:
    def test_markdown_file_uses_md_parser(self) -> None:
        content_json, title = NoteImportService.parse_content("# My Note\n\nBody text.", ext="md")
        assert title == "My Note"
        assert content_json["type"] == "doc"

    def test_txt_file_uses_first_line_as_title(self) -> None:
        content_json, title = NoteImportService.parse_content("My Title\n\nBody text.", ext="txt")
        assert title == "My Title"
        assert content_json["type"] == "doc"

    def test_empty_extension_treated_as_plaintext(self) -> None:
        content_json, title = NoteImportService.parse_content("A Title\nBody.", ext="")
        assert title == "A Title"
        assert content_json["type"] == "doc"

    def test_txt_title_truncated_at_120_chars(self) -> None:
        long_line = "A" * 200
        _, title = NoteImportService.parse_content(long_line, ext="txt")
        assert len(title) == 120

    def test_txt_empty_content_gives_untitled(self) -> None:
        _, title = NoteImportService.parse_content("   ", ext="txt")
        assert title == "Untitled"

    def test_unsupported_extension_raises(self) -> None:
        with pytest.raises(UnsupportedFileTypeError, match="pdf"):
            NoteImportService.parse_content("content", ext="pdf")
