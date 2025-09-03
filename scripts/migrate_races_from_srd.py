from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_parts(*parts: Any) -> str | None:
    texts: list[str] = []
    for p in parts:
        if isinstance(p, list):
            texts.extend([x for x in p if isinstance(x, str)])
        elif isinstance(p, str) and p:
            texts.append(p)
    text = "\n\n".join([t for t in texts if t])
    return text or None


def to_indexes(lst: Any) -> list[str]:
    out: list[str] = []
    if isinstance(lst, list):
        for x in lst:
            if isinstance(x, dict) and isinstance(x.get("index"), str):
                out.append(x["index"])
    return out


def convert_race(r: dict[str, Any]) -> dict[str, Any]:
    description = join_parts(r.get("age"), r.get("alignment"), r.get("size_description"), r.get("language_desc"))
    # Ability bonuses
    ability_bonuses: dict[str, int] = {}
    for ab in r.get("ability_bonuses") or []:
        if isinstance(ab, dict):
            idx = (ab.get("ability_score") or {}).get("index")
            bonus = ab.get("bonus")
            if isinstance(idx, str) and isinstance(bonus, int):
                ability_bonuses[idx] = bonus
    # Proficiencies
    weapon_profs: list[str] = []
    tool_profs: list[str] = []
    for p in r.get("starting_proficiencies") or []:
        if isinstance(p, dict) and isinstance(p.get("index"), str):
            idx = p["index"]
            if idx.startswith("weapon-"):
                weapon_profs.append(idx)
            if idx.startswith("tool-"):
                tool_profs.append(idx)
    # Language options
    lang_opts: list[str] = []
    opts = r.get("language_options") or {}
    for opt in opts.get("from") or []:
        if isinstance(opt, dict) and isinstance(opt.get("index"), str):
            lang_opts.append(opt["index"])
    return {
        "index": r.get("index"),
        "name": r.get("name"),
        "speed": int(r.get("speed", 30)),
        "size": r.get("size", "Medium"),
        "languages": to_indexes(r.get("languages")),
        "description": description,
        "traits": to_indexes(r.get("traits")) or None,
        "subraces": to_indexes(r.get("subraces")) or None,
        "ability_bonuses": ability_bonuses or None,
        "weapon_proficiencies": weapon_profs or None,
        "tool_proficiencies": tool_profs or None,
        "language_options": lang_opts or None,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Races.json"
    dst = root / "data/races.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    races = [convert_race(r) for r in raw if r.get("index") and r.get("name")]
    out = {"races": races}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(races)} races")


if __name__ == "__main__":
    main()
