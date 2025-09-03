from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str | None:
    if isinstance(parts, list):
        text = "\n\n".join([p for p in parts if isinstance(p, str)])
        return text or None
    if isinstance(parts, str):
        return parts
    return None


def convert_subrace(sr: dict[str, Any]) -> dict[str, Any]:
    # Ability bonuses
    ability_bonuses: dict[str, int] = {}
    for ab in sr.get("ability_bonuses") or []:
        if isinstance(ab, dict):
            idx = (ab.get("ability_score") or {}).get("index")
            bonus = ab.get("bonus")
            if isinstance(idx, str) and isinstance(bonus, int):
                ability_bonuses[idx] = bonus
    # Proficiencies
    weapon_profs: list[str] = []
    tool_profs: list[str] = []
    for p in sr.get("starting_proficiencies") or []:
        if isinstance(p, dict) and isinstance(p.get("index"), str):
            idx = p["index"]
            if idx.startswith("weapon-"):
                weapon_profs.append(idx)
            if idx.startswith("tool-"):
                tool_profs.append(idx)
    return {
        "index": sr.get("index"),
        "name": sr.get("name"),
        "parent_race": (sr.get("race") or {}).get("index"),
        "description": join_paragraphs(sr.get("desc")),
        "traits": [t.get("index") for t in (sr.get("racial_traits") or []) if isinstance(t, dict) and t.get("index")],
        "ability_bonuses": ability_bonuses or None,
        "weapon_proficiencies": weapon_profs or None,
        "tool_proficiencies": tool_profs or None,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Subraces.json"
    dst = root / "data/subraces.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    subraces = [convert_subrace(x) for x in raw if x.get("index") and x.get("name")]
    out = {"subraces": subraces}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(subraces)} subraces")


if __name__ == "__main__":
    main()
