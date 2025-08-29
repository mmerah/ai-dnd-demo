"""Service for loading and managing game data from JSON files."""

import json
from pathlib import Path
from typing import TypedDict

from app.models.npc import NPCSheet


class ItemData(TypedDict):
    """Type definition for item data."""

    name: str
    type: str
    rarity: str
    weight: float
    value: int
    description: str
    # Optional fields
    subtype: str | None
    damage: str | None
    damage_type: str | None
    properties: list[str] | None
    armor_class: int | None
    quantity_available: int | None


class SpellData(TypedDict):
    """Type definition for spell data."""

    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    higher_levels: str | None
    classes: list[str]


class DataService:
    """Service for loading and managing game data with caching."""

    def __init__(self, data_directory: Path | None = None):
        """
        Initialize data service.

        Args:
            data_directory: Path to data directory containing JSON files
        """
        if data_directory is None:
            data_directory = Path(__file__).parent.parent / "data"
        self.data_directory = data_directory

        # Cache for loaded data
        self._items: dict[str, ItemData] = {}
        self._monsters: dict[str, NPCSheet] = {}
        self._spells: dict[str, SpellData] = {}

        # Load all data on initialization
        self._load_all_data()

    def _load_all_data(self) -> None:
        """Load all data files into memory."""
        self._load_items()
        self._load_monsters()
        self._load_spells()

    def _load_items(self) -> None:
        """Load items from items.json."""
        items_path = self.data_directory / "items.json"
        if not items_path.exists():
            raise FileNotFoundError(f"Items data file not found: {items_path}")

        try:
            with open(items_path, encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("items", []):
                self._items[item["name"]] = item

        except Exception as e:
            raise RuntimeError(f"Failed to load items data: {e}") from e

    def _load_monsters(self) -> None:
        """Load monsters from monsters.json."""
        monsters_path = self.data_directory / "monsters.json"
        if not monsters_path.exists():
            raise FileNotFoundError(f"Monsters data file not found: {monsters_path}")

        try:
            with open(monsters_path, encoding="utf-8") as f:
                data = json.load(f)

            for monster_data in data.get("monsters", []):
                # Convert hit_points to proper format
                if isinstance(monster_data.get("hit_points"), int):
                    monster_data["hit_points"] = {
                        "current": monster_data["hit_points"],
                        "maximum": monster_data["hit_points"],
                        "temporary": 0,
                    }

                # Create NPCSheet from data
                monster = NPCSheet(**monster_data)
                self._monsters[monster.name] = monster

        except Exception as e:
            raise RuntimeError(f"Failed to load monsters data: {e}") from e

    def _load_spells(self) -> None:
        """Load spells from spells.json."""
        spells_path = self.data_directory / "spells.json"
        if not spells_path.exists():
            raise FileNotFoundError(f"Spells data file not found: {spells_path}")

        try:
            with open(spells_path, encoding="utf-8") as f:
                data = json.load(f)

            for spell in data.get("spells", []):
                self._spells[spell["name"]] = spell

        except Exception as e:
            raise RuntimeError(f"Failed to load spells data: {e}") from e

    def get_item(self, name: str, allow_missing: bool = False) -> ItemData | None:
        """
        Get item data by name.

        Args:
            name: Item name to look up
            allow_missing: If False, raise error when item not found

        Returns:
            Item data or None if not found and allow_missing is True

        Raises:
            KeyError: If item not found and allow_missing is False
        """
        if name in self._items:
            return self._items[name]

        if not allow_missing:
            available_items = ", ".join(sorted(self._items.keys()))
            raise KeyError(f"Item '{name}' not found in database. Available items: {available_items}")

        return None

    def get_monster(self, name: str, allow_missing: bool = False) -> NPCSheet | None:
        """
        Get monster data by name.

        Args:
            name: Monster name to look up
            allow_missing: If False, raise error when monster not found

        Returns:
            Monster NPCSheet or None if not found and allow_missing is True

        Raises:
            KeyError: If monster not found and allow_missing is False
        """
        if name in self._monsters:
            # Return a copy to avoid modifying the cached version
            return self._monsters[name].model_copy(deep=True)

        if not allow_missing:
            available_monsters = ", ".join(sorted(self._monsters.keys()))
            raise KeyError(f"Monster '{name}' not found in database. Available monsters: {available_monsters}")

        return None

    def get_spell(self, name: str, allow_missing: bool = False) -> SpellData | None:
        """
        Get spell data by name.

        Args:
            name: Spell name to look up
            allow_missing: If False, raise error when spell not found

        Returns:
            Spell data or None if not found and allow_missing is True

        Raises:
            KeyError: If spell not found and allow_missing is False
        """
        # Try exact match first
        if name in self._spells:
            return self._spells[name]

        # Try case-insensitive match
        for spell_name, spell_data in self._spells.items():
            if spell_name.lower() == name.lower():
                return spell_data

        if not allow_missing:
            available_spells = ", ".join(sorted(self._spells.keys()))
            raise KeyError(f"Spell '{name}' not found in database. Available spells: {available_spells}")

        return None

    def list_items(self) -> list[str]:
        """Get list of all available item names."""
        return sorted(self._items.keys())

    def list_monsters(self) -> list[str]:
        """Get list of all available monster names."""
        return sorted(self._monsters.keys())

    def list_spells(self) -> list[str]:
        """Get list of all available spell names."""
        return sorted(self._spells.keys())

    def validate_item_reference(self, name: str) -> bool:
        """Check if an item exists in the database."""
        return name in self._items

    def validate_monster_reference(self, name: str) -> bool:
        """Check if a monster exists in the database."""
        return name in self._monsters

    def validate_spell_reference(self, name: str) -> bool:
        """Check if a spell exists in the database."""
        return name in self._spells or any(s.lower() == name.lower() for s in self._spells)
