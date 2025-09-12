from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def convert_school(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": s.get("index"),
        "name": s.get("name"),
        "description": s.get("desc", ""),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Magic-Schools.json"
    dst = root / "data/magic_schools.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    magic_schools = [convert_school(s) for s in raw if s.get("index") and s.get("name")]
    add_pack_fields(magic_schools, "srd")
    out = {"magic_schools": magic_schools}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['magic_schools'])} schools")


if __name__ == "__main__":
    main()
