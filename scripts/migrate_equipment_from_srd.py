from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields

GP_FACTORS = {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1.0, "pp": 10.0}


def to_gp(cost: dict[str, Any] | None) -> float:
    if not isinstance(cost, dict):
        return 0.0
    qty = cost.get("quantity", 0)
    unit = (cost.get("unit") or "gp").lower()
    factor = GP_FACTORS.get(unit, 1.0)
    try:
        return float(qty) * factor
    except Exception:
        return 0.0


def map_type(e: dict[str, Any]) -> tuple[str, str | None]:
    cat = ((e.get("equipment_category") or {}).get("index") or "").lower()
    gear_cat = ((e.get("gear_category") or {}).get("index") or "").lower()
    if cat == "weapon":
        subtype = (e.get("weapon_range") or "").capitalize() or None
        return "Weapon", subtype
    if cat == "armor":
        sub = (e.get("armor_category") or "").capitalize() or None
        if sub == "Shield":
            return "Armor", "Shield"
        return "Armor", sub
    if gear_cat == "equipment-packs":
        return "Equipment Pack", None
    if cat == "ammunition":
        return "Ammunition", None
    # Default bucket
    return "Adventuring Gear", None


def first_desc(e: dict[str, Any]) -> str:
    d = e.get("desc")
    if isinstance(d, list) and d:
        return str(d[0])
    if isinstance(d, str):
        return d
    return ""


def map_properties(e: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for p in e.get("properties", []) or []:
        if isinstance(p, dict) and p.get("name"):
            out.append(p["name"])
    return out


def convert_equipment(e: dict[str, Any]) -> dict[str, Any] | None:
    name = e.get("name")
    if not name:
        return None
    item_type, subtype = map_type(e)
    rarity = "Common"
    weight = float(e.get("weight", 0) or 0)
    value = to_gp(e.get("cost"))
    description = first_desc(e)

    damage = None
    damage_type = None
    if isinstance(e.get("damage"), dict):
        dmg = e["damage"]
        damage = dmg.get("damage_dice")
        damage_type = (dmg.get("damage_type") or {}).get("name")

    armor_class = None
    dex_bonus = None
    if isinstance(e.get("armor_class"), dict):
        ac = e["armor_class"]
        armor_class = ac.get("base")
        dex_bonus = bool(ac.get("dex_bonus")) if "dex_bonus" in ac else None

    props = map_properties(e)

    contents: list[str] = []
    for c in e.get("contents", []) or []:
        item = c.get("item") or {}
        nm = item.get("name")
        qty = c.get("quantity", 1)
        if nm:
            if qty and qty != 1:
                contents.append(f"{nm} x{qty}")
            else:
                contents.append(nm)

    # index slug
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
        "value": value,
        "description": description,
        "subtype": subtype,
        "damage": damage,
        "damage_type": damage_type,
        "properties": props,
        "armor_class": armor_class,
        "dex_bonus": dex_bonus,
        "contents": contents or [],
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Equipment.json"
    dst = root / "data/items.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    items = []
    for e in raw:
        conv = convert_equipment(e)
        if conv:
            items.append(conv)
    add_pack_fields(items, "srd")
    out = {"items": items}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(items)} items")


if __name__ == "__main__":
    main()
