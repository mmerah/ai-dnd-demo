"""Factory helpers for NPC test data."""

from __future__ import annotations

from app.models.attributes import Abilities
from app.models.character import CharacterSheet
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.instances.npc_instance import NPCInstance
from app.models.npc import NPCImportance, NPCSheet

from .characters import make_character_sheet


def make_npc_sheet(
    *,
    npc_id: str = "npc-1",
    display_name: str = "Town Guard",
    role: str = "Guard",
    description: str = "A stalwart town guard",
    initial_location_id: str = "town-square",
    character: CharacterSheet | None = None,
    importance: NPCImportance = NPCImportance.MINOR,
) -> NPCSheet:
    """Create an NPCSheet embedding a CharacterSheet.

    The embedded character name is aligned with the NPC display name by default.
    """
    character = character or make_character_sheet(name=display_name)
    return NPCSheet(
        id=npc_id,
        display_name=display_name,
        role=role,
        description=description,
        initial_location_id=initial_location_id,
        importance=importance,
        character=character,
    )


def make_npc_instance(
    *,
    npc_sheet: NPCSheet | None = None,
    instance_id: str = "npc-1",
    scenario_npc_id: str | None = None,
    current_location_id: str = "town-square",
) -> NPCInstance:
    """Create an NPCInstance with a basic, valid EntityState."""
    npc_sheet = npc_sheet or make_npc_sheet()
    scenario_npc_id = scenario_npc_id or npc_sheet.id

    # Minimal but consistent state based on character template
    char = npc_sheet.character
    state = EntityState(
        abilities=char.starting_abilities
        if isinstance(char.starting_abilities, Abilities)
        else make_character_sheet().starting_abilities,
        level=char.starting_level,
        experience_points=char.starting_experience_points,
        hit_points=HitPoints(current=10, maximum=10, temporary=0),
        hit_dice=HitDice(total=1, current=1, type="d8"),
        currency=char.starting_currency.model_copy(),
        spellcasting=char.starting_spellcasting,
    )

    return NPCInstance(
        instance_id=instance_id,
        sheet=npc_sheet,
        state=state,
        scenario_npc_id=scenario_npc_id,
        current_location_id=current_location_id,
    )
