from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_trait(t: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": t.get("index"),
        "name": t.get("name"),
        "description": join_paragraphs(t.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Traits.json"
    dst = root / "data/traits.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    traits = [convert_trait(x) for x in raw if x.get("index") and x.get("name")]
    add_pack_fields(traits, "srd")
    out = {"traits": traits}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(traits)} traits")


if __name__ == "__main__":
    main()
