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

    # Add additional D&D 5e alignment variations that appear in monster data
    additional_alignments = [
        {
            "index": "unknown",
            "name": "Unknown",
            "description": "Alignment unknown or not applicable.",
        },
        {
            "index": "unaligned",
            "name": "Unaligned",
            "description": "Creatures that lack the capacity for rational thought or moral and ethical choice. Most beasts, constructs, plants, and oozes are unaligned.",
        },
        {
            "index": "any-alignment",
            "name": "Any Alignment",
            "description": "Can be of any alignment. Used for humanoid NPCs and creatures that vary in alignment based on individual.",
        },
        {
            "index": "any-non-good-alignment",
            "name": "Any Non-Good Alignment",
            "description": "Can be of any alignment except good alignments. Used for evil or morally ambiguous NPCs.",
        },
        {
            "index": "any-non-lawful-alignment",
            "name": "Any Non-Lawful Alignment",
            "description": "Can be of any alignment except lawful alignments. Used for chaotic or neutral NPCs.",
        },
        {
            "index": "any-chaotic-alignment",
            "name": "Any Chaotic Alignment",
            "description": "Can be chaotic good, chaotic neutral, or chaotic evil. Used for inherently chaotic creatures.",
        },
        {
            "index": "neutral-good-(50%)-or-neutral-evil-(50%)",
            "name": "Neutral Good or Neutral Evil",
            "description": "Equally likely to be neutral good or neutral evil. Used for creatures with variable morality.",
        },
        {
            "index": "any-evil-alignment",
            "name": "Any Evil Alignment",
            "description": "Can be lawful evil, neutral evil, or chaotic evil. Used for inherently evil creatures.",
        },
    ]

    alignments.extend(additional_alignments)
    out = {"alignments": alignments}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['alignments'])} alignments")


if __name__ == "__main__":
    main()
