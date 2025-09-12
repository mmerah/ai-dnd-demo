from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_magic_item(mi: dict[str, Any]) -> dict[str, Any] | None:
    name = mi.get("name")
    if not name:
        return None
    # Rough type mapping: potions become Potion, others Adventuring Gear
    category = (mi.get("equipment_category") or {}).get("index") or ""
    item_type = "Potion" if category.lower() == "potion" or "potion" in name.lower() else "Adventuring Gear"
    rarity = (mi.get("rarity") or {}).get("name") or "Uncommon"
    description = join_paragraphs(mi.get("desc"))
    weight = float(mi.get("weight", 0) or 0)

    base_slug = (
        unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii").lower().replace(" ", "-")
    )
    base_slug = re.sub(r"[^a-z0-9-]", "", base_slug)

    return {
        "index": base_slug,
        "name": name,
        "type": item_type,
        "rarity": rarity,
        "weight": weight,
        "value": 0,
        "description": description,
        "subtype": None,
        "damage": None,
        "damage_type": None,
        "properties": [],
        "armor_class": None,
        "dex_bonus": None,
        "contents": [],
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Magic-Items.json"
    dst = root / "data/magic_items.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    items = []
    for mi in raw:
        conv = convert_magic_item(mi)
        if conv:
            items.append(conv)
    add_pack_fields(items, "srd")
    out = {"items": items}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(items)} magic items")


if __name__ == "__main__":
    main()
