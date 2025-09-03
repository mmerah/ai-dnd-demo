from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def gp_value(cost: dict[str, Any]) -> float:
    qty = cost.get("quantity", 0)
    unit = (cost.get("unit") or "gp").lower()
    rate = {"gp": 1.0, "sp": 0.1, "cp": 0.01, "ep": 0.5}.get(unit, 1.0)
    try:
        return float(qty) * rate
    except Exception:
        return 0.0


def convert_spell(s: dict[str, Any]) -> dict[str, Any]:
    # Components: array + material -> single string like "V, S, M (material)"
    comps = s.get("components", []) or []
    if not isinstance(comps, list):
        comps = [str(comps)]
    comp_str = ", ".join(comps)
    material = s.get("material")
    if material:
        comp_str = f"{comp_str} (" + material + ")" if comp_str else f"M ({material})"

    # Classes: list of ApiRef objects to list of names
    classes = [c.get("name") for c in s.get("classes", []) if isinstance(c, dict) and c.get("name")]

    # Higher level: array to single string
    higher = None
    if isinstance(s.get("higher_level"), list):
        higher = "\n".join(s["higher_level"]) if s["higher_level"] else None

    # Description: array to single string paragraphs
    desc = "\n\n".join(s.get("desc", [])) if isinstance(s.get("desc"), list) else (s.get("desc") or "")

    return {
        "name": s.get("name"),
        "level": s.get("level", 0),
        "school": (s.get("school", {}) or {}).get("name", ""),
        "casting_time": s.get("casting_time", ""),
        "range": s.get("range", ""),
        "components": comp_str,
        "duration": s.get("duration", ""),
        "description": desc,
        "higher_levels": higher,
        "classes": classes,
        "ritual": bool(s.get("ritual", False)),
        "concentration": bool(s.get("concentration", False)),
    }


def ingest_spells(srd_spells_path: Path, out_path: Path) -> None:
    data = json.load(srd_spells_path.open())
    out: dict[str, Any] = {"spells": []}
    for s in data:
        try:
            out["spells"].append(convert_spell(s))
        except Exception:
            continue
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, out_path.open("w"), indent=2, ensure_ascii=False)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    srd_dir = root / "docs/5e-database-snippets/src/2014"
    out_dir = root / "data"
    ingest_spells(srd_dir / "5e-SRD-Spells.json", out_dir / "spells_srd.json")
    print("Wrote", out_dir / "spells_srd.json")


if __name__ == "__main__":
    main()
