"""Unit tests for `GameFactory`."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import create_autospec

import pytest

from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.game import ILocationService
from app.interfaces.services.scenario import IScenarioService
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.location import LocationConnection
from app.models.quest import QuestStatus
from app.models.scenario import LocationDescriptions
from app.services.game.game_factory import GameFactory
from tests.factories import make_character_sheet, make_location, make_quest, make_scenario


class TestGameFactory:
    """Validate the orchestration performed inside `GameFactory`."""

    def setup_method(self) -> None:
        self.scenario_service = create_autospec(IScenarioService, instance=True)
        self.compute_service = create_autospec(ICharacterComputeService, instance=True)
        self.location_service = create_autospec(ILocationService, instance=True)

        self.factory = GameFactory(
            scenario_service=self.scenario_service,
            compute_service=self.compute_service,
            location_service=self.location_service,
        )

        self.character = make_character_sheet()

        quest = make_quest()

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

        self.scenario = make_scenario(
            starting_location_id=self.start_location.id,
            locations=[self.start_location],
            quests=[quest],
        )

        self.scenario_service.get_scenario.return_value = self.scenario
        self.scenario_service.list_scenario_npcs.return_value = []

        self.initial_state = EntityState(
            abilities=self.character.starting_abilities,
            level=1,
            experience_points=0,
            hit_points=HitPoints(current=11, maximum=11, temporary=0),
            hit_dice=HitDice(total=1, current=1, type="d10"),
            currency=self.character.starting_currency.model_copy(),
        )
        self.compute_service.initialize_entity_state.return_value = self.initial_state

    def test_initialize_game_populates_game_state(self) -> None:
        game_state = self.factory.initialize_game(
            character=self.character,
            scenario_id=self.scenario.id,
            content_packs=["custom-pack"],
        )

        assert game_state.scenario_id == self.scenario.id
        assert game_state.location == self.start_location.name
        assert game_state.content_packs == ["srd", f"scenario:{self.scenario.id}", "custom-pack"]
        assert game_state.conversation_history[0].location == self.start_location.name
        assert self.scenario.title in game_state.conversation_history[0].content
        self.location_service.initialize_location_from_scenario.assert_called_once()
        self.scenario_service.list_scenario_npcs.assert_called_once_with(self.scenario.id)
        self.compute_service.initialize_entity_state.assert_called()

        active_quests = game_state.scenario_instance.active_quests
        assert active_quests
        assert active_quests[0].status == QuestStatus.ACTIVE

    def test_generate_game_id_includes_character_name(self) -> None:
        game_id = self.factory.generate_game_id("Hero Knight")

        assert game_id.startswith("hero-knight-")
        date_part, time_part = game_id.split("-")[2:4]
        datetime.strptime(f"{date_part}-{time_part}", "%Y%m%d-%H%M")

    def test_initialize_game_raises_for_missing_scenario(self) -> None:
        self.scenario_service.get_scenario.return_value = None

        with pytest.raises(RuntimeError) as exc:
            self.factory.initialize_game(self.character, "missing")

        assert "No scenario available" in str(exc.value)
