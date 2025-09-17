"""
Shared helpers for migration scripts.

Adds content pack metadata to each element to support the content pack system.
"""

from __future__ import annotations

from typing import Any


def add_pack_fields(items: list[dict[str, Any]], pack_id: str = "srd") -> list[dict[str, Any]]:
    """Ensure each item has content pack fields.

    Mutates the input list, returns it for convenience/chaining.
    """
    for it in items:
        it.setdefault("content_pack", pack_id)
        it.setdefault("reference_packs", [])
    return items


def apply_pack_fields_to_container(container: dict[str, Any], key: str, pack_id: str = "srd") -> dict[str, Any]:
    """If container[key] is a list of dicts, add content pack fields to each element.

    Removes any mistakenly added root-level pack fields to keep schema clean.
    """
    try:
        items = container.get(key)
        if isinstance(items, list):
            add_pack_fields(items, pack_id)
        # Clean any root-level mistakes
        container.pop("content_pack", None)
        container.pop("reference_packs", None)
    except Exception:
        # Non-fatal; migrations are best effort
        pass
    return container
