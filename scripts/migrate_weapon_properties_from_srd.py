from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_prop(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": p.get("index"),
        "name": p.get("name"),
        "description": join_paragraphs(p.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Weapon-Properties.json"
    dst = root / "data/weapon_properties.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    weapon_properties = [convert_prop(x) for x in raw if x.get("index") and x.get("name")]
    add_pack_fields(weapon_properties, "srd")
    out = {"weapon_properties": weapon_properties}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['weapon_properties'])} weapon properties")


if __name__ == "__main__":
    main()
