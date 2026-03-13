from __future__ import annotations


JsonObject = dict[str, object]


def _as_object(value: object) -> JsonObject | None:
    if isinstance(value, dict):
        return value
    return None


def _walk(node: JsonObject) -> list[JsonObject]:
    nodes = [node]
    raw_content = node.get("content")
    if isinstance(raw_content, list):
        for item in raw_content:
            item_node = _as_object(item)
            if item_node is not None:
                nodes.extend(_walk(item_node))
    return nodes


def extract_asset_ids_from_doc(content_json: dict[str, object]) -> set[str]:
    root = _as_object(content_json)
    if root is None:
        return set()

    asset_ids: set[str] = set()
    for node in _walk(root):
        if str(node.get("type", "")) != "image":
            continue
        attrs = _as_object(node.get("attrs")) or {}
        asset_id = attrs.get("assetId")
        if isinstance(asset_id, str) and asset_id.strip():
            asset_ids.add(asset_id.strip())
    return asset_ids
