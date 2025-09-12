from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def as_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def fmt_speed(speed: Any) -> str:
    if isinstance(speed, str):
        return speed.replace(".", "")
    if not isinstance(speed, dict):
        return ""
    parts: list[str] = []
    for k, v in speed.items():
        if isinstance(v, str) and v:
            parts.append(f"{k} {v.replace('.', '')}")
    return ", ".join(parts)


def fmt_senses(senses: Any) -> str:
    if not isinstance(senses, dict):
        return str(senses or "")
    parts: list[str] = []
    for k, v in senses.items():
        if k == "passive_perception":
            parts.append(f"passive Perception {v}")
        else:
            parts.append(f"{k.capitalize()} {v}")
    return ", ".join(parts)


def parse_attack_type(desc: str) -> str:
    if "Melee or Ranged" in desc:
        return "Melee or Ranged"
    if "Ranged" in desc:
        return "Ranged"
    return "Melee"


def extract_reach(desc: str) -> str | None:
    m = re.search(r"reach\s+([\d/ ]+ft\.)", desc)
    return m.group(1) if m else None


def extract_range(desc: str) -> str | None:
    m = re.search(r"range\s+([\d/ ]+ft\.)", desc)
    return m.group(1) if m else None


def extract_first_damage(dmg_list: Any) -> tuple[str | None, str | None]:
    if not isinstance(dmg_list, list) or not dmg_list:
        return None, None
    first = dmg_list[0]
    if isinstance(first, dict):
        dice = first.get("damage_dice")
        dtype = (first.get("damage_type") or {}).get("index")
        return dice, dtype
    return None, None


def normalize_alignment(s: Any) -> str:
    if not isinstance(s, str):
        return "unaligned"
    return s.strip().lower().replace(" ", "-")


def tokenize_languages(s: Any) -> list[str]:
    if isinstance(s, list):
        return [str(x).strip().lower().replace(" ", "-") for x in s]
    if not isinstance(s, str) or not s:
        return []
    # remove telepathy phrases
    s = re.sub(r",?\s*telepathy[^,]*", "", s, flags=re.I)
    parts = [p.strip() for p in s.split(",")]
    out = [p.lower().replace(" ", "-") for p in parts if p]
    # Map elemental dialects to primordial
    mapped = []
    for lang in out:
        if lang in {"auran", "aquan", "ignan", "terran"}:
            mapped.append("primordial")
        else:
            mapped.append(lang)
    # de-duplicate while preserving order
    result = []
    for lang in mapped:
        if lang and lang not in result:
            result.append(lang)
    return result


def convert_monster(m: dict[str, Any]) -> dict[str, Any]:
    # Armor class: pick first value or int
    ac_val: int | None = None
    ac = m.get("armor_class")
    if isinstance(ac, int):
        ac_val = ac
    elif isinstance(ac, list) and ac:
        first = ac[0]
        if isinstance(first, dict) and isinstance(first.get("value"), int):
            ac_val = first["value"]

    actions = []
    for act in m.get("actions", []) or []:
        if not isinstance(act, dict):
            continue
        name = act.get("name")
        desc = act.get("desc", "") or ""
        if not name or not desc:
            continue
        if "Weapon Attack" not in desc and "Spell Attack" not in desc and not act.get("attack_bonus"):
            # Not an attack action we can simplify meaningfully
            continue
        attack_roll_bonus = act.get("attack_bonus")
        if isinstance(attack_roll_bonus, list):
            attack_roll_bonus = attack_roll_bonus[0] if attack_roll_bonus else None
        damage_dice, damage_type = extract_first_damage(act.get("damage"))
        atk_type = parse_attack_type(desc)
        reach = extract_reach(desc)
        rng = extract_range(desc)
        actions.append(
            {
                "name": name,
                "type": atk_type,
                "attack_roll_bonus": as_int(attack_roll_bonus, 0),
                "reach": reach,
                "range": rng,
                "damage": damage_dice or "",
                "damage_type": damage_type or "",
                "special": None,
            }
        )

    specials = []
    for sa in m.get("special_abilities", []) or []:
        if isinstance(sa, dict) and sa.get("name") and sa.get("desc"):
            specials.append({"name": sa["name"], "description": sa["desc"]})

    # Condition immunities
    cond_immunities: list[str] = []
    for ci in m.get("condition_immunities", []) or []:
        if isinstance(ci, dict):
            idx = ci.get("index") or (ci.get("condition") or {}).get("index")
            if isinstance(idx, str):
                cond_immunities.append(idx)

    name = m.get("name")
    # Build a stable index slug from name
    base_slug = (
        unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii").lower().replace(" ", "-")
        if name
        else ""
    )
    base_slug = re.sub(r"[^a-z0-9-]", "", base_slug)
    return {
        "index": base_slug,
        "name": m.get("name"),
        "type": m.get("type"),
        "size": m.get("size"),
        "alignment": normalize_alignment(m.get("alignment")),
        "armor_class": ac_val if ac_val is not None else as_int(ac, 10),
        "hit_points": {
            "current": as_int(m.get("hit_points"), 1),
            "maximum": as_int(m.get("hit_points"), 1),
            "temporary": 0,
        },
        "hit_dice": m.get("hit_points_roll") or m.get("hit_dice") or "",
        "speed": fmt_speed(m.get("speed")),
        "challenge_rating": float(m.get("challenge_rating") or 0),
        "abilities": {
            "STR": as_int(m.get("strength"), 10),
            "DEX": as_int(m.get("dexterity"), 10),
            "CON": as_int(m.get("constitution"), 10),
            "INT": as_int(m.get("intelligence"), 10),
            "WIS": as_int(m.get("wisdom"), 10),
            "CHA": as_int(m.get("charisma"), 10),
        },
        "skills": {
            # Extract skill proficiencies
            ((p.get("proficiency") or {}).get("name", "Skill: ").split(": ")[-1]): p.get("value")
            for p in (m.get("proficiencies") or [])
            if isinstance(p, dict)
            and isinstance(p.get("proficiency"), dict)
            and str(p["proficiency"].get("index", "")).startswith("skill-")
        },
        "senses": fmt_senses(m.get("senses")),
        "languages": tokenize_languages(m.get("languages")),
        "attacks": actions,
        "special_abilities": specials,
        "damage_vulnerabilities": m.get("damage_vulnerabilities") or [],
        "damage_resistances": m.get("damage_resistances") or [],
        "damage_immunities": m.get("damage_immunities") or [],
        "condition_immunities": cond_immunities,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Monsters.json"
    dst = root / "data/monsters.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    monsters = [convert_monster(m) for m in raw if m.get("name")]
    add_pack_fields(monsters, "srd")
    out = {"monsters": monsters}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(monsters)} monsters")


if __name__ == "__main__":
    main()
