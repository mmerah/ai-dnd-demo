from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def convert_skill(s: dict[str, Any]) -> dict[str, Any]:
    ability = (s.get("ability_score") or {}).get("index")
    return {
        "index": s.get("index"),
        "name": s.get("name"),
        "ability": ability,
        "description": join_paragraphs(s.get("desc")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Skills.json"
    dst = root / "data/skills.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    skills = [convert_skill(x) for x in raw if x.get("index") and x.get("name")]
    out = {"skills": skills}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(skills)} skills")


if __name__ == "__main__":
    main()
