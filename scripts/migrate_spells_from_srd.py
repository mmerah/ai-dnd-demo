from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([str(p) for p in parts if p is not None])
    return str(parts or "")


def normalize_components(components: Any, material: Any) -> tuple[list[str], str | None]:
    comp_list: list[str] = []
    if isinstance(components, list):
        comp_list = [str(c) for c in components if c]
    elif components:
        comp_list = [str(components)]
    mat = str(material) if material else None
    return comp_list, mat


def to_int_keyed(d: dict[str, Any] | None) -> dict[int, Any] | None:
    if not d:
        return None
    out: dict[int, Any] = {}
    for k, v in d.items():
        try:
            out[int(k)] = v
        except Exception:
            continue
    return out or None


def convert_spell(s: dict[str, Any]) -> dict[str, Any]:
    components_list, material = normalize_components(s.get("components"), s.get("material"))
    area = s.get("area_of_effect")
    if area and not isinstance(area, dict):
        area = None
    dc = s.get("dc")
    if isinstance(dc, dict):
        dc_type = dc.get("dc_type", {}) or {}
        dc = {
            "dc_type": dc_type.get("index"),
            "dc_success": dc.get("dc_success"),
        }
    else:
        dc = None

    classes = [c.get("index") for c in s.get("classes", []) if isinstance(c, dict) and c.get("index")]
    subclasses = [c.get("index") for c in s.get("subclasses", []) if isinstance(c, dict) and c.get("index")]
    damage = s.get("damage") or {}
    damage_at_slot_level = to_int_keyed(damage.get("damage_at_slot_level"))
    damage_at_character_level = to_int_keyed(damage.get("damage_at_character_level"))

    return {
        "index": s.get("index"),
        "name": s.get("name"),
        "level": s.get("level", 0),
        "school": (s.get("school", {}) or {}).get("index"),
        "casting_time": s.get("casting_time", ""),
        "range": s.get("range", ""),
        "duration": s.get("duration", ""),
        "description": join_paragraphs(s.get("desc")),
        "higher_levels": join_paragraphs(s.get("higher_level")) or None,
        "components_list": components_list,
        "material": material,
        "ritual": bool(s.get("ritual", False)),
        "concentration": bool(s.get("concentration", False)),
        "classes": classes,
        "subclasses": subclasses,
        "area_of_effect": area,
        "attack_type": s.get("attack_type"),
        "dc": dc,
        "damage_at_slot_level": damage_at_slot_level,
        "damage_at_character_level": damage_at_character_level,
        "heal_at_slot_level": to_int_keyed(s.get("heal_at_slot_level")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    srd = root / "docs/5e-database-snippets/src/2014/5e-SRD-Spells.json"
    out = root / "data/spells.json"
    data = json.load(srd.open())
    spells = [convert_spell(s) for s in data]
    # drop invalid/nameless
    spells = [s for s in spells if s.get("index") and s.get("name")]
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"spells": spells}, out.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {out} with {len(spells)} spells")


if __name__ == "__main__":
    main()
