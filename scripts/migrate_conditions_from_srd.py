from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_condition(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": c.get("index"),
        "name": c.get("name"),
        "description": join_paragraphs(c.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Conditions.json"
    dst = root / "data/conditions.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    conditions = [convert_condition(x) for x in raw if x.get("index") and x.get("name")]
    out = {"conditions": conditions}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(conditions)} conditions")


if __name__ == "__main__":
    main()
