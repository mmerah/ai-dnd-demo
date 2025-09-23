"""Unit tests for `LocationService`."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.interfaces.services.game.monster_manager_service import IMonsterManagerService
from app.models.game_state import GameState, GameTime
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import DangerLevel, LocationConnection, LocationState
from app.models.monster import MonsterSheet
from app.models.scenario import LocationDescriptions, ScenarioMonster
from app.services.game.location_service import LocationService
from tests.factories import (
    make_character_instance,
    make_character_sheet,
    make_location,
    make_monster_instance,
    make_monster_sheet,
    make_npc_instance,
    make_scenario,
)


@dataclass
class _FakeMonsterManagerService(IMonsterManagerService):
    """Minimal monster service stub to record creations."""

    created: list[MonsterInstance]

    def create(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:  # pragma: no cover
        monster = make_monster_instance(sheet=sheet, current_location_id=current_location_id)
        self.created.append(monster)
        return monster

    def add_monster_to_game(self, game_state: GameState, monster: MonsterInstance) -> str:  # pragma: no cover
        game_state.monsters.append(monster)
        return monster.sheet.name


class TestLocationService:
    """Unit tests exercising high-level location behaviour."""

    def setup_method(self) -> None:
        self.monster_manager_service = _FakeMonsterManagerService(created=[])
        self.service = LocationService(monster_manager_service=self.monster_manager_service)

        self.character_sheet = make_character_sheet()

        self.start_location = make_location(
            location_id="town-square",
            name="Town Square",
            description="The bustling heart of town.",
            connections=[LocationConnection(to_location_id="old-forest", description="Trail to the woods")],
            descriptions=LocationDescriptions(
                first_visit="Cobblestones shine in the morning light.",
                return_visit="The townsfolk nod as you pass.",
            ),
        )
        forest_location = make_location(
            location_id="old-forest",
            name="Old Forest",
            description="Gnarled trees whisper in the wind.",
            connections=[LocationConnection(to_location_id="town-square", description="Back to town")],
        )

        scenario = make_scenario(
            starting_location_id=self.start_location.id,
            locations=[self.start_location, forest_location],
        )

        self.game_state = GameState(
            game_id="hero-game",
            character=make_character_instance(sheet=self.character_sheet, instance_id="hero-1"),
            npcs=[],
            monsters=[],
            scenario_id=scenario.id,
            scenario_title=scenario.title,
            scenario_instance=ScenarioInstance(
                instance_id="scn-1",
                template_id=scenario.id,
                sheet=scenario,
                current_location_id=self.start_location.id,
                current_act_id="act1",
            ),
            content_packs=list(scenario.content_packs),
            location=self.start_location.name,
            conversation_history=[],
            game_time=GameTime(),
            description="",
            story_notes=[],
            game_events=[],
        )

    def test_validate_traversal_blocks_unconnected_locations(self) -> None:
        with pytest.raises(ValueError) as exc:
            self.service.validate_traversal(self.game_state, self.start_location.id, "hidden-cave")

        assert "Valid destinations" in str(exc.value)

    def test_move_entity_updates_location_and_description(self) -> None:
        self.service.move_entity(
            self.game_state, entity_id=self.game_state.character.instance_id, to_location_id=self.start_location.id
        )

        assert self.game_state.location == self.start_location.name
        descriptions = self.start_location.descriptions
        assert descriptions is not None
        assert descriptions.first_visit in self.game_state.description
        assert self.game_state.scenario_instance.location_states[self.start_location.id].visited is True

    def test_move_npc_between_known_locations(self) -> None:
        npc = make_npc_instance(instance_id="npc-1", current_location_id=self.start_location.id)
        self.game_state.npcs.append(npc)

        self.service.move_entity(self.game_state, entity_id="npc-1", to_location_id=self.start_location.id)

        assert npc.current_location_id == self.start_location.id

    def test_discover_secret_records_secret(self) -> None:
        loc_state = LocationState(location_id=self.start_location.id)
        self.game_state.scenario_instance.location_states[self.start_location.id] = loc_state

        description = self.service.discover_secret(self.game_state, "secret-door", "Hidden passage")

        assert description == "Hidden passage"
        assert "secret-door" in loc_state.discovered_secrets

    def test_initialize_location_populates_monsters(self) -> None:
        monster = make_monster_sheet(name="Wolf")
        target_loc = make_location(
            location_id="wolves-den",
            name="Wolves' Den",
            description="A den hidden in the brush.",
        )
        target_loc.notable_monsters.append(
            ScenarioMonster(
                id="wolf-1",
                display_name="Wolf",
                monster=monster,
            )
        )

        self.service.initialize_location_from_scenario(self.game_state, target_loc)

        assert self.monster_manager_service.created
        created = self.monster_manager_service.created[0]
        assert created.current_location_id == target_loc.id
        assert created.sheet.name == monster.name

    def test_update_location_state_defaults_to_current_location(self) -> None:
        self.game_state.scenario_instance.current_location_id = self.start_location.id
        self.game_state.scenario_instance.location_states[self.start_location.id] = LocationState(
            location_id=self.start_location.id,
            danger_level=DangerLevel.LOW,
        )

        effect = "Blessed"
        location_id, updates = self.service.update_location_state(
            self.game_state,
            danger_level=DangerLevel.CLEARED.value,
            add_effect=effect,
        )

        assert location_id == self.start_location.id
        assert "Danger level" in " ".join(updates)
        assert effect in updates[-1]
