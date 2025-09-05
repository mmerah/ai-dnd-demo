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

    # Add additional D&D 5e language variations that appear in monster data
    additional_languages = [
        {
            "index": "unknown",
            "name": "Unknown",
            "type": None,
            "script": None,
            "description": "Language unknown or not applicable.",
        },
        # Common language variations
        {
            "index": "any-one-language-(usually-common)",
            "name": "Any One Language (Usually Common)",
            "type": "Standard",
            "script": None,
            "description": "Can speak any one language, typically Common.",
        },
        {
            "index": "any-one-language",
            "name": "Any One Language",
            "type": "Standard",
            "script": None,
            "description": "Can speak any one language.",
        },
        {
            "index": "any-two-languages",
            "name": "Any Two Languages",
            "type": "Standard",
            "script": None,
            "description": "Can speak any two languages.",
        },
        {
            "index": "any-four-languages",
            "name": "Any Four Languages",
            "type": "Standard",
            "script": None,
            "description": "Can speak any four languages.",
        },
        {
            "index": "any-six-languages",
            "name": "Any Six Languages",
            "type": "Standard",
            "script": None,
            "description": "Can speak any six languages.",
        },
        {
            "index": "all",
            "name": "All Languages",
            "type": "Standard",
            "script": None,
            "description": "Can speak and understand all languages.",
        },
        # Creature-specific languages
        {
            "index": "blink-dog",
            "name": "Blink Dog",
            "type": "Exotic",
            "script": None,
            "description": "The language of blink dogs.",
        },
        {
            "index": "giant-eagle",
            "name": "Giant Eagle",
            "type": "Exotic",
            "script": None,
            "description": "The language of giant eagles.",
        },
        {
            "index": "giant-elk",
            "name": "Giant Elk",
            "type": "Exotic",
            "script": None,
            "description": "The language of giant elk.",
        },
        {
            "index": "giant-owl",
            "name": "Giant Owl",
            "type": "Exotic",
            "script": None,
            "description": "The language of giant owls.",
        },
        {
            "index": "gnoll",
            "name": "Gnoll",
            "type": "Exotic",
            "script": None,
            "description": "The language of gnolls.",
        },
        {
            "index": "sahuagin",
            "name": "Sahuagin",
            "type": "Exotic",
            "script": None,
            "description": "The language of sahuagin.",
        },
        {
            "index": "sphinx",
            "name": "Sphinx",
            "type": "Exotic",
            "script": None,
            "description": "The language of sphinxes.",
        },
        {
            "index": "winter-wolf",
            "name": "Winter Wolf",
            "type": "Exotic",
            "script": None,
            "description": "The language of winter wolves.",
        },
        {
            "index": "worg",
            "name": "Worg",
            "type": "Exotic",
            "script": None,
            "description": "The language of worgs.",
        },
        {
            "index": "otyugh",
            "name": "Otyugh",
            "type": "Exotic",
            "script": None,
            "description": "The language of otyughs.",
        },
        {
            "index": "druidic",
            "name": "Druidic",
            "type": "Standard",
            "script": None,
            "description": "The secret language of druids.",
        },
        # Special language abilities
        {
            "index": "understands-common-but-can't-speak",
            "name": "Understands Common but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Common but lacks the ability to speak.",
        },
        {
            "index": "understands-draconic-but-can't-speak",
            "name": "Understands Draconic but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Draconic but lacks the ability to speak.",
        },
        {
            "index": "understands-deep-speech-but-can't-speak",
            "name": "Understands Deep Speech but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Deep Speech but lacks the ability to speak.",
        },
        {
            "index": "understands-infernal-but-can't-speak",
            "name": "Understands Infernal but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Infernal but lacks the ability to speak.",
        },
        {
            "index": "understands-infernal-but-can't-speak-it",
            "name": "Understands Infernal but can't speak it",
            "type": "Special",
            "script": None,
            "description": "Can understand Infernal but lacks the ability to speak it.",
        },
        {
            "index": "understands-abyssal",
            "name": "Understands Abyssal",
            "type": "Special",
            "script": None,
            "description": "Can understand Abyssal.",
        },
        {
            "index": "understands-celestial",
            "name": "Understands Celestial",
            "type": "Special",
            "script": None,
            "description": "Can understand Celestial.",
        },
        {
            "index": "understands-common-but-doesn't-speak-it",
            "name": "Understands Common but doesn't speak it",
            "type": "Special",
            "script": None,
            "description": "Can understand Common but doesn't speak it.",
        },
        {
            "index": "understands-the-languages-of-its-creator-but-can't-speak",
            "name": "Understands the languages of its creator but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand the languages known by its creator but lacks the ability to speak.",
        },
        {
            "index": "one-language-known-by-its-creator",
            "name": "One language known by its creator",
            "type": "Special",
            "script": None,
            "description": "Knows one language that was known by its creator.",
        },
        {
            "index": "understands-all-languages-it-spoke-in-life-but-can't-speak",
            "name": "Understands all languages it spoke in life but can't speak",
            "type": "Special",
            "script": None,
            "description": "Retains understanding of languages from life but cannot speak.",
        },
        {
            "index": "understands-all-languages-it-knew-in-life-but-can't-speak",
            "name": "Understands all languages it knew in life but can't speak",
            "type": "Special",
            "script": None,
            "description": "Retains understanding of languages from life but cannot speak.",
        },
        {
            "index": "any-languages-it-knew-in-life",
            "name": "Any languages it knew in life",
            "type": "Special",
            "script": None,
            "description": "Retains any languages known in life.",
        },
        {
            "index": "the-languages-it-knew-in-life",
            "name": "The languages it knew in life",
            "type": "Special",
            "script": None,
            "description": "Retains the languages known in life.",
        },
        {
            "index": "understands-common-and-giant-but-can't-speak",
            "name": "Understands Common and Giant but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Common and Giant but lacks the ability to speak.",
        },
        {
            "index": "understands-common-and-draconic-but-can't-speak",
            "name": "Understands Common and Draconic but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Common and Draconic but lacks the ability to speak.",
        },
        {
            "index": "understands-commands-given-in-any-language-but-can't-speak",
            "name": "Understands commands given in any language but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand commands in any language but cannot speak.",
        },
        {
            "index": "common-(can't-speak-in-boar-form)",
            "name": "Common (can't speak in boar form)",
            "type": "Special",
            "script": None,
            "description": "Can speak Common but not while in boar form.",
        },
        {
            "index": "thieves'-cant-plus-any-two-languages",
            "name": "Thieves' Cant plus any two languages",
            "type": "Special",
            "script": None,
            "description": "Knows Thieves' Cant and any two other languages.",
        },
        {
            "index": "druidic-plus-any-two-languages",
            "name": "Druidic plus any two languages",
            "type": "Special",
            "script": None,
            "description": "Knows Druidic and any two other languages.",
        },
        {
            "index": "understands-sylvan-but-can't-speak-it",
            "name": "Understands Sylvan but can't speak it",
            "type": "Special",
            "script": None,
            "description": "Can understand Sylvan but lacks the ability to speak it.",
        },
        {
            "index": "understands-common-and-auran-but-can't-speak",
            "name": "Understands Common and Auran but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Common and Auran but lacks the ability to speak.",
        },
        {
            "index": "understands-common",
            "name": "Understands Common",
            "type": "Special",
            "script": None,
            "description": "Can understand Common.",
        },
        {
            "index": "and-primordial-but-can't-speak",
            "name": "And Primordial but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Primordial but lacks the ability to speak.",
        },
        {
            "index": "understands-abyssal-but-can't-speak",
            "name": "Understands Abyssal but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Abyssal but lacks the ability to speak.",
        },
        {
            "index": "and-infernal-but-can't-speak",
            "name": "And Infernal but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Infernal but lacks the ability to speak.",
        },
        {
            "index": "and-sylvan-but-can't-speak",
            "name": "And Sylvan but can't speak",
            "type": "Special",
            "script": None,
            "description": "Can understand Sylvan but lacks the ability to speak.",
        },
    ]

    languages.extend(additional_languages)
    out = {"languages": languages}
    dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, dst.open("w"), indent=2, ensure_ascii=False)
    print(f"Wrote {dst} with {len(out['languages'])} languages")


if __name__ == "__main__":
    main()
