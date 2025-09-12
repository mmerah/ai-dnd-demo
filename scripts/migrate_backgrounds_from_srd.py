from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def join_paragraphs(parts: Any) -> str | None:
    if isinstance(parts, list):
        text = "\n\n".join([p for p in parts if isinstance(p, str)])
        return text or None
    if isinstance(parts, str):
        return parts
    return None


def convert_background(b: dict[str, Any]) -> dict[str, Any]:
    desc = None
    feature = b.get("feature") or {}
    if isinstance(feature, dict):
        desc = join_paragraphs(feature.get("desc"))

    return {
        "index": b.get("index"),
        "name": b.get("name"),
        "description": desc,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Backgrounds.json"
    dst = root / "data/backgrounds.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    backgrounds = [convert_background(x) for x in raw if x.get("index") and x.get("name")]
    add_pack_fields(backgrounds, "srd")
    out = {"backgrounds": backgrounds}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(backgrounds)} backgrounds")


if __name__ == "__main__":
    main()
