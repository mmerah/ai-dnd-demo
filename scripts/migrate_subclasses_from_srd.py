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


def convert_subclass(sc: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": sc.get("index"),
        "name": sc.get("name"),
        "parent_class": (sc.get("class") or {}).get("index"),
        "description": join_paragraphs(sc.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Subclasses.json"
    dst = root / "data/subclasses.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    subclasses = [convert_subclass(s) for s in raw if s.get("index") and s.get("name")]
    add_pack_fields(subclasses, "srd")
    out = {"subclasses": subclasses}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(subclasses)} subclasses")


if __name__ == "__main__":
    main()
