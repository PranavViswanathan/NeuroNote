"""Tests for markdown/text → TipTap JSON import parser."""
from __future__ import annotations

from app.import_.markdown_parser import parse_markdown_to_tiptap, parse_plaintext_to_tiptap


class TestParseMarkdownToTiptap:
    def test_empty_input(self) -> None:
        result = parse_markdown_to_tiptap("")
        assert result == {"type": "doc", "content": []}

    def test_heading_levels(self) -> None:
        for level in (1, 2, 3):
            md = f"{'#' * level} Title {level}"
            doc = parse_markdown_to_tiptap(md)
            heading = doc["content"][0]
            assert heading["type"] == "heading"
            assert heading["attrs"]["level"] == level
            assert heading["content"][0]["text"] == f"Title {level}"

    def test_paragraph(self) -> None:
        doc = parse_markdown_to_tiptap("Hello world")
        para = doc["content"][0]
        assert para["type"] == "paragraph"
        assert para["content"][0]["text"] == "Hello world"

    def test_bullet_list(self) -> None:
        md = "- item one\n- item two"
        doc = parse_markdown_to_tiptap(md)
        bl = doc["content"][0]
        assert bl["type"] == "bulletList"
        assert len(bl["content"]) == 2
        assert bl["content"][0]["type"] == "listItem"

    def test_ordered_list(self) -> None:
        md = "1. first\n2. second"
        doc = parse_markdown_to_tiptap(md)
        ol = doc["content"][0]
        assert ol["type"] == "orderedList"
        assert len(ol["content"]) == 2

    def test_code_block(self) -> None:
        md = "```python\nprint('hello')\n```"
        doc = parse_markdown_to_tiptap(md)
        cb = doc["content"][0]
        assert cb["type"] == "codeBlock"
        assert "print('hello')" in cb["content"][0]["text"]

    def test_blockquote(self) -> None:
        md = "> quoted text"
        doc = parse_markdown_to_tiptap(md)
        bq = doc["content"][0]
        assert bq["type"] == "blockquote"

    def test_horizontal_rule(self) -> None:
        md = "---"
        doc = parse_markdown_to_tiptap(md)
        hr = doc["content"][0]
        assert hr["type"] == "horizontalRule"

    def test_mixed_content(self) -> None:
        md = "# Title\n\nParagraph text\n\n- item\n\n---"
        doc = parse_markdown_to_tiptap(md)
        types = [node["type"] for node in doc["content"]]
        assert types == ["heading", "paragraph", "bulletList", "horizontalRule"]

    def test_empty_lines_between_paragraphs(self) -> None:
        md = "First paragraph\n\nSecond paragraph"
        doc = parse_markdown_to_tiptap(md)
        assert len(doc["content"]) == 2
        assert doc["content"][0]["content"][0]["text"] == "First paragraph"
        assert doc["content"][1]["content"][0]["text"] == "Second paragraph"


class TestParsePlaintextToTiptap:
    def test_empty_input(self) -> None:
        result = parse_plaintext_to_tiptap("")
        assert result == {"type": "doc", "content": []}

    def test_single_line(self) -> None:
        doc = parse_plaintext_to_tiptap("hello")
        assert len(doc["content"]) == 1
        assert doc["content"][0]["type"] == "paragraph"
        assert doc["content"][0]["content"][0]["text"] == "hello"

    def test_multiple_lines(self) -> None:
        doc = parse_plaintext_to_tiptap("line one\nline two\nline three")
        assert len(doc["content"]) == 3

    def test_blank_lines_become_empty_paragraphs(self) -> None:
        doc = parse_plaintext_to_tiptap("a\n\nb")
        assert len(doc["content"]) == 3
        # Middle paragraph is empty (no content)
        assert doc["content"][1]["content"] == []
