from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_feature(f: dict[str, Any]) -> dict[str, Any]:
    class_index = (f.get("class") or {}).get("index") if isinstance(f.get("class"), dict) else None
    subclass_index = (f.get("subclass") or {}).get("index") if isinstance(f.get("subclass"), dict) else None
    level = f.get("level")
    granted_by = {"class": class_index, "subclass": subclass_index} if class_index or subclass_index else None
    return {
        "index": f.get("index"),
        "name": f.get("name"),
        "description": join_paragraphs(f.get("desc")),
        "class_index": class_index,
        "subclass_index": subclass_index,
        "level": level,
        "granted_by": granted_by,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Features.json"
    dst = root / "data/features.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    features = [convert_feature(x) for x in raw if x.get("index") and x.get("name")]
    add_pack_fields(features, "srd")
    out = {"features": features}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(features)} features")


if __name__ == "__main__":
    main()
