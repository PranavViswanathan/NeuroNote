from __future__ import annotations

from collections.abc import Iterable


JsonObject = dict[str, object]


def _as_object(value: object) -> JsonObject | None:
    if isinstance(value, dict):
        return value
    return None


def _children(node: JsonObject) -> list[JsonObject]:
    raw_content = node.get("content")
    if not isinstance(raw_content, list):
        return []
    result: list[JsonObject] = []
    for item in raw_content:
        item_node = _as_object(item)
        if item_node is not None:
            result.append(item_node)
    return result


def _text_from_children(nodes: Iterable[JsonObject]) -> str:
    return "".join(_render_inline(node) for node in nodes).strip()


def _render_inline(node: JsonObject) -> str:
    node_type = str(node.get("type", ""))
    if node_type == "text":
        value = node.get("text")
        return value if isinstance(value, str) else ""

    if node_type == "mathInline":
        attrs = _as_object(node.get("attrs")) or {}
        latex = attrs.get("latex")
        latex_text = latex if isinstance(latex, str) else ""
        return f"${latex_text}$"

    if node_type == "image":
        attrs = _as_object(node.get("attrs")) or {}
        alt = attrs.get("alt")
        alt_text = alt if isinstance(alt, str) and alt else "image"
        filename = attrs.get("filename")
        if not isinstance(filename, str) or not filename:
            asset_id = attrs.get("assetId")
            ext = attrs.get("ext")
            if isinstance(asset_id, str) and asset_id:
                extension = ext if isinstance(ext, str) and ext else "bin"
                filename = f"{asset_id}.{extension}"
            else:
                filename = "image.bin"
        return f"![{alt_text}](assets/{filename})"

    return _text_from_children(_children(node))


def _render_block(node: JsonObject) -> str:
    node_type = str(node.get("type", ""))
    children = _children(node)

    if node_type == "heading":
        attrs = _as_object(node.get("attrs")) or {}
        level_raw = attrs.get("level")
        level = int(level_raw) if isinstance(level_raw, int) and 1 <= level_raw <= 6 else 1
        return f"{'#' * level} {_text_from_children(children)}".strip()

    if node_type == "paragraph":
        return _text_from_children(children)

    if node_type == "mathBlock":
        attrs = _as_object(node.get("attrs")) or {}
        latex = attrs.get("latex")
        latex_text = latex if isinstance(latex, str) else ""
        return f"$${latex_text}$$"

    if node_type == "image":
        return _render_inline(node)

    if node_type == "bulletList":
        lines: list[str] = []
        for item in children:
            if str(item.get("type", "")) != "listItem":
                continue
            line = _text_from_children(_children(item))
            if line:
                lines.append(f"- {line}")
        return "\n".join(lines)

    if node_type == "orderedList":
        lines = []
        index = 1
        for item in children:
            if str(item.get("type", "")) != "listItem":
                continue
            line = _text_from_children(_children(item))
            if line:
                lines.append(f"{index}. {line}")
                index += 1
        return "\n".join(lines)

    if node_type == "blockquote":
        line = _text_from_children(children)
        return f"> {line}" if line else ""

    if node_type == "codeBlock":
        line = _text_from_children(children)
        return f"```\n{line}\n```"

    if node_type == "horizontalRule":
        return "---"

    return _text_from_children(children)


def render_note_markdown(content_json: dict[str, object]) -> str:
    """Return markdown representation for TipTap-like JSON content."""
    root = _as_object(content_json)
    if root is None:
        return ""

    blocks = _children(root)
    rendered = [_render_block(block).rstrip() for block in blocks]
    filtered = [line for line in rendered if line]
    if not filtered:
        return ""
    return "\n\n".join(filtered).rstrip() + "\n"
