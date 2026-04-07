"""Markdown and plain-text → TipTap JSON parser.

Line-by-line regex parsing that supports the subset of markdown matching
what the export produces: headings, paragraphs, lists, code blocks,
blockquotes, and horizontal rules.
"""
from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")
_BULLET_RE = re.compile(r"^[-*+]\s+(.+)$")
_ORDERED_RE = re.compile(r"^\d+\.\s+(.+)$")
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")
_HR_RE = re.compile(r"^-{3,}$")
_CODE_FENCE_RE = re.compile(r"^```(.*)$")


def _text_node(text: str) -> dict[str, object]:
    return {"type": "text", "text": text}


def _paragraph(text: str) -> dict[str, object]:
    if not text.strip():
        return {"type": "paragraph", "content": []}
    return {"type": "paragraph", "content": [_text_node(text)]}


def _heading(level: int, text: str) -> dict[str, object]:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [_text_node(text)],
    }


def _list_item(text: str) -> dict[str, object]:
    return {
        "type": "listItem",
        "content": [_paragraph(text)],
    }


def parse_markdown_to_tiptap(content: str) -> dict[str, object]:
    """Parse markdown into a TipTap document JSON structure."""
    if not content.strip():
        return {"type": "doc", "content": []}

    lines = content.split("\n")
    nodes: list[dict[str, object]] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Empty line — skip (paragraph separator)
        if not line.strip():
            i += 1
            continue

        # Code fence
        fence_match = _CODE_FENCE_RE.match(line)
        if fence_match:
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not _CODE_FENCE_RE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            nodes.append({
                "type": "codeBlock",
                "content": [_text_node("\n".join(code_lines))],
            })
            continue

        # Heading
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            nodes.append(_heading(level, heading_match.group(2).strip()))
            i += 1
            continue

        # Horizontal rule
        if _HR_RE.match(line.strip()):
            nodes.append({"type": "horizontalRule"})
            i += 1
            continue

        # Bullet list (consecutive lines)
        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            items: list[dict[str, object]] = []
            while i < len(lines) and _BULLET_RE.match(lines[i]):
                m = _BULLET_RE.match(lines[i])
                items.append(_list_item(m.group(1) if m else ""))
                i += 1
            nodes.append({"type": "bulletList", "content": items})
            continue

        # Ordered list (consecutive lines)
        ordered_match = _ORDERED_RE.match(line)
        if ordered_match:
            items = []
            while i < len(lines) and _ORDERED_RE.match(lines[i]):
                m = _ORDERED_RE.match(lines[i])
                items.append(_list_item(m.group(1) if m else ""))
                i += 1
            nodes.append({"type": "orderedList", "content": items})
            continue

        # Blockquote (consecutive lines)
        bq_match = _BLOCKQUOTE_RE.match(line)
        if bq_match:
            bq_lines: list[str] = []
            while i < len(lines) and _BLOCKQUOTE_RE.match(lines[i]):
                m = _BLOCKQUOTE_RE.match(lines[i])
                bq_lines.append(m.group(1) if m else "")
                i += 1
            bq_text = "\n".join(bq_lines)
            nodes.append({
                "type": "blockquote",
                "content": [_paragraph(bq_text)],
            })
            continue

        # Plain paragraph
        nodes.append(_paragraph(line))
        i += 1

    return {"type": "doc", "content": nodes}


def parse_plaintext_to_tiptap(content: str) -> dict[str, object]:
    """Wrap each line of plain text into a paragraph node."""
    if not content.strip():
        return {"type": "doc", "content": []}

    lines = content.split("\n")
    nodes = [_paragraph(line) for line in lines]
    return {"type": "doc", "content": nodes}


def extract_title_from_markdown(content: str) -> str:
    """Return the first heading text, or the first non-empty line, or 'Untitled'."""
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            return heading_match.group(2).strip()
        return line
    return "Untitled"
