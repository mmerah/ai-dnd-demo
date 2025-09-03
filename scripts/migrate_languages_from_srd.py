from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def convert_language(lang: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": lang.get("index"),
        "name": lang.get("name"),
        "type": lang.get("type"),
        "script": lang.get("script"),
        "description": lang.get("desc"),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Languages.json"
    dst = root / "data/languages.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    languages = [convert_language(x) for x in raw if x.get("index") and x.get("name")]
    # Ensure an 'unknown' language is available for normalization fallbacks
    languages.append(
        {
            "index": "unknown",
            "name": "Unknown",
            "type": None,
            "script": None,
            "description": "Language unknown or not applicable.",
        }
    )
    out = {"languages": languages}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['languages'])} languages")


if __name__ == "__main__":
    main()
