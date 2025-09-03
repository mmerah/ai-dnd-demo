from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def join_paragraphs(parts: Any) -> str:
    if isinstance(parts, list):
        return "\n\n".join([p for p in parts if isinstance(p, str)])
    return str(parts or "")


def stringify_prerequisites(pr: Any) -> str | None:
    if not pr:
        return None
    parts: list[str] = []
    if isinstance(pr, list):
        for p in pr:
            if isinstance(p, dict):
                # Ability score minimum
                abil = (p.get("ability_score") or {}).get("name") or (p.get("ability_score") or {}).get("index")
                minv = p.get("minimum_score")
                if abil and minv:
                    parts.append(f"{abil} {minv}")
                # Other types (e.g., proficiency) fallback to name/index
                name = p.get("name") or (p.get("proficiency") or {}).get("name")
                if name:
                    parts.append(str(name))
    return ", ".join(parts) if parts else None


def convert_feat(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": f.get("index"),
        "name": f.get("name"),
        "description": join_paragraphs(f.get("desc")),
        "prerequisites": stringify_prerequisites(f.get("prerequisites")),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Feats.json"
    dst = root / "data/feats.json"
    raw: list[dict[str, Any]] = json.load(src.open())
    feats = [convert_feat(x) for x in raw if x.get("index") and x.get("name")]
    out = {"feats": feats}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(feats)} feats")


if __name__ == "__main__":
    main()
