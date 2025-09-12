from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_pack_utils import add_pack_fields


def to_indexes(objs: Any, key: str = "index") -> list[str]:
    if not isinstance(objs, list):
        return []
    out: list[str] = []
    for o in objs:
        if isinstance(o, dict):
            idx = o.get(key)
            if isinstance(idx, str) and idx:
                out.append(idx)
    return out


def _convert_proficiency_choices(pc_list: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(pc_list, list):
        return out
    for pc in pc_list:
        if not isinstance(pc, dict):
            continue
        choose = pc.get("choose", 0)
        opts = []
        frm = pc.get("from") or {}
        if isinstance(frm, dict) and isinstance(frm.get("options"), list):
            for opt in frm["options"]:
                if isinstance(opt, dict):
                    if opt.get("option_type") == "reference":
                        item = opt.get("item") or {}
                        idx = item.get("index")
                        if isinstance(idx, str):
                            opts.append(idx)
                    elif opt.get("option_type") == "counted_reference":
                        of = opt.get("of") or {}
                        idx = of.get("index")
                        if isinstance(idx, str):
                            opts.append(idx)
        out.append({"choose": int(choose), "from_options": opts})
    return out


def _convert_starting_equipment(eq_list: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(eq_list, list):
        return out
    for e in eq_list:
        if isinstance(e, dict):
            eq = e.get("equipment") or {}
            idx = eq.get("index")
            qty = e.get("quantity", 1)
            if isinstance(idx, str):
                try:
                    qty = int(qty)
                except Exception:
                    qty = 1
                out.append({"index": idx, "quantity": qty})
    return out


def _convert_starting_equipment_options_desc(opts_list: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(opts_list, list):
        return out
    for o in opts_list:
        if isinstance(o, dict):
            desc = o.get("desc")
            if isinstance(desc, str) and desc:
                out.append(desc)
    return out


def _convert_multiclassing(mc: Any) -> dict[str, Any] | None:
    if not isinstance(mc, dict):
        return None
    prereqs = []
    for r in mc.get("prerequisites", []) or []:
        if isinstance(r, dict):
            ab = (r.get("ability_score") or {}).get("index")
            if isinstance(ab, str):
                prereqs.append({"ability": ab, "minimum_score": int(r.get("minimum_score", 0))})
    profs = to_indexes(mc.get("proficiencies"))
    prof_choices = _convert_proficiency_choices(mc.get("proficiency_choices"))
    return {
        "prerequisites": prereqs,
        "proficiencies": profs or [],
        "proficiency_choices": prof_choices or [],
    }


def _compose_description(c: dict[str, Any]) -> str | None:
    parts: list[str] = []
    # spellcasting info desc blocks
    sc = c.get("spellcasting")
    if isinstance(sc, dict) and isinstance(sc.get("info"), list):
        for info in sc["info"]:
            if isinstance(info, dict) and isinstance(info.get("desc"), list):
                for d in info["desc"]:
                    if isinstance(d, str):
                        parts.append(d)
    # proficiency choices and starting equipment options descriptions as supplemental text
    for pc in c.get("proficiency_choices", []) or []:
        if isinstance(pc, dict) and isinstance(pc.get("desc"), str):
            parts.append(pc["desc"])
    for so in c.get("starting_equipment_options", []) or []:
        if isinstance(so, dict) and isinstance(so.get("desc"), str):
            parts.append(so["desc"])
    text = "\n\n".join([p for p in parts if p])
    return text or None


def convert_class(c: dict[str, Any]) -> dict[str, Any]:
    # Saving throws from ability-scores ApiRefs
    saving_throws = to_indexes(c.get("saving_throws"))

    # Proficiencies as proficiency indexes, excluding saving-throw-* entries to avoid duplication
    profs = to_indexes(c.get("proficiencies"))
    proficiencies = [p for p in profs if not p.startswith("saving-throw-")]

    # Spellcasting ability index if present
    sc = c.get("spellcasting") or {}
    sc_ability = None
    if isinstance(sc, dict):
        sc_ability = (sc.get("spellcasting_ability") or {}).get("index")

    description = _compose_description(c)
    proficiency_choices = _convert_proficiency_choices(c.get("proficiency_choices"))
    starting_equipment = _convert_starting_equipment(c.get("starting_equipment"))
    starting_equipment_options_desc = _convert_starting_equipment_options_desc(c.get("starting_equipment_options"))
    subclasses = to_indexes(c.get("subclasses"))
    multi = _convert_multiclassing(c.get("multi_classing"))

    return {
        "index": c.get("index"),
        "name": c.get("name"),
        "hit_die": c.get("hit_die"),
        "saving_throws": saving_throws or None,
        "proficiencies": proficiencies or None,
        "spellcasting_ability": sc_ability,
        "description": description,
        "proficiency_choices": proficiency_choices or None,
        "starting_equipment": starting_equipment or None,
        "starting_equipment_options_desc": starting_equipment_options_desc or None,
        "subclasses": subclasses or None,
        "multi_classing": multi,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Classes.json"
    dst = root / "data/classes.json"

    raw: list[dict[str, Any]] = json.load(src.open())
    classes = [convert_class(c) for c in raw if c.get("index") and c.get("name")]
    # Append a minimal extra 'commoner' class for NPCs and townsfolk (not SRD, but useful for scenario NPCs)
    commoner = {
        "index": "commoner",
        "name": "Commoner",
        "hit_die": 8,
        "saving_throws": ["wis", "cha"],
        "proficiencies": ["light-armor", "simple-weapons"],
        "spellcasting_ability": None,
        "description": "A non-adventuring archetype for townsfolk and merchants.",
        "proficiency_choices": None,
        "starting_equipment": None,
        "starting_equipment_options_desc": None,
        "subclasses": None,
        "multi_classing": None,
    }
    classes.append(commoner)
    add_pack_fields(classes, "srd")
    out = {"classes": classes}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(classes)} classes")


if __name__ == "__main__":
    main()
