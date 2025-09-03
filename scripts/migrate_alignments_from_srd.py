from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def convert_alignment(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": a.get("index"),
        "name": a.get("name"),
        "description": a.get("desc", ""),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Alignments.json"
    dst = root / "data/alignments.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    alignments = [convert_alignment(a) for a in raw if a.get("index") and a.get("name")]
    # Ensure an 'unknown' alignment is available for normalization fallbacks
    alignments.append(
        {
            "index": "unknown",
            "name": "Unknown",
            "description": "Alignment unknown or not applicable.",
        }
    )
    out = {"alignments": alignments}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['alignments'])} alignments")


if __name__ == "__main__":
    main()
