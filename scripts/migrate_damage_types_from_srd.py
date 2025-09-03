from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_dt(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": d.get("index"),
        "name": d.get("name"),
        "description": join_paragraphs(d.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Damage-Types.json"
    dst = root / "data/damage_types.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    out = {"damage_types": [convert_dt(x) for x in raw if x.get("index") and x.get("name")]}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['damage_types'])} damage types")


if __name__ == "__main__":
    main()
