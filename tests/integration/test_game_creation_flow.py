"""Integration test for game creation flow."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.container import Container
from app.models.attributes import Abilities
from app.models.character import CharacterSheet, Currency, Personality
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import DangerLevel
from app.models.scenario import (
    LocationDescriptions,
    ScenarioAct,
    ScenarioLocation,
    ScenarioProgression,
    ScenarioSheet,
)
from app.models.spell import Spellcasting, SpellcastingAbility, SpellSlot


class TestGameCreationFlow:
    """Integration test for creating a new game."""

    def setup_method(self) -> None:
        """Set up test environment with container."""
        # Create a temporary directory for saves
        self.temp_dir = tempfile.mkdtemp()
        self.save_path = Path(self.temp_dir) / "saves"
        self.save_path.mkdir()

        # Initialize container with mocked dependencies where needed
        self.container = Container()

        # Create mock scenarios for tests
        self._setup_mock_scenarios()

    def _setup_mock_scenarios(self) -> None:
        """Set up mock scenarios for testing."""
        # Create mock scenario sheets
        self.mock_scenarios = {}

        # Goblin cave adventure scenario
        goblin_location = ScenarioLocation(
            id="goblin-cave",
            name="Goblin Cave Entrance",
            description="A dark cave entrance looms before you.",
            descriptions=LocationDescriptions(
                first_visit="You stand at the entrance of a dark cave.",
                return_visit="The familiar cave entrance awaits.",
            ),
            danger_level=DangerLevel.MODERATE,
        )

        self.mock_scenarios["goblin-cave-adventure"] = ScenarioSheet(
            id="goblin-cave-adventure",
            title="Goblin Cave Adventure",
            description="A classic adventure in a goblin-infested cave.",
            starting_location_id="goblin-cave",
            locations=[goblin_location],
            progression=ScenarioProgression(
                acts=[
                    ScenarioAct(
                        id="act1",
                        name="Act 1",
                        locations=["goblin-cave"],
                        objectives=["Explore the cave"],
                    )
                ]
            ),
            content_packs=["srd"],
        )

        # Test scenario for persistence test
        test_location = ScenarioLocation(
            id="test-location",
            name="Test Location",
            description="A test location.",
            danger_level=DangerLevel.SAFE,
        )

        self.mock_scenarios["test-scenario"] = ScenarioSheet(
            id="test-scenario",
            title="Test Scenario",
            description="A test scenario.",
            starting_location_id="test-location",
            locations=[test_location],
            progression=ScenarioProgression(
                acts=[
                    ScenarioAct(
                        id="act1",
                        name="Act 1",
                        locations=["test-location"],
                        objectives=["Test objective"],
                    )
                ]
            ),
            content_packs=["srd"],
        )

        # Generic test scenarios for list test
        for i in range(3):
            location = ScenarioLocation(
                id=f"location-{i}",
                name=f"Location {i}",
                description=f"Location {i} description.",
                danger_level=DangerLevel.SAFE,
            )

            self.mock_scenarios[f"scenario-{i}"] = ScenarioSheet(
                id=f"scenario-{i}",
                title=f"Scenario {i}",
                description=f"Test scenario {i}.",
                starting_location_id=f"location-{i}",
                locations=[location],
                progression=ScenarioProgression(
                    acts=[
                        ScenarioAct(
                            id="act1",
                            name="Act 1",
                            locations=[f"location-{i}"],
                            objectives=[f"Objective {i}"],
                        )
                    ]
                ),
                content_packs=["srd"],
            )

        # Create a mock function for getting scenarios
        def mock_get_scenario(scenario_id: str) -> ScenarioSheet | None:
            return self.mock_scenarios.get(scenario_id)

        # Store the mock function for use in tests
        self.mock_get_scenario = mock_get_scenario

    def teardown_method(self) -> None:
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_new_game_flow(self) -> None:
        """Test the complete flow of creating a new game."""
        # Mock the path resolver to use our temp directory and scenario service
        with (
            patch.object(self.container.path_resolver, "saves_dir", self.save_path),
            patch.object(self.container.scenario_service, "get_scenario", side_effect=self.mock_get_scenario),
        ):
            # Get services from container
            game_service = self.container.game_service
            character_service = self.container.character_service

            # Create a test character
            test_character = CharacterSheet(
                id="test-ranger",
                name="Aldric Swiftarrow",
                race="wood-elf",
                class_index="ranger",
                starting_level=3,
                background="outlander",
                alignment="neutral-good",
                personality=Personality(
                    traits=["I am always cautious", "Nature is my friend"],
                    ideals=["Balance in all things"],
                    bonds=["I must protect the forest"],
                    flaws=["I trust too easily"],
                ),
                backstory="A ranger from the deep woods",
                languages=["common", "elvish"],
                starting_abilities=Abilities(STR=13, DEX=16, CON=14, INT=12, WIS=15, CHA=10),
                starting_skill_indexes=["survival", "nature"],
                starting_inventory=[],
                starting_currency=Currency(gold=10, silver=5, copper=20),
                starting_experience_points=900,
                starting_spellcasting=Spellcasting(
                    ability=SpellcastingAbility.WIS,
                    spell_save_dc=13,
                    spell_attack_bonus=5,
                    spells_known=["hunters-mark", "cure-wounds"],
                    spell_slots={
                        1: SpellSlot(level=1, total=3, current=3),
                        2: SpellSlot(level=2, total=0, current=0),
                    },
                ),
            )

            # Mock character service to return our test character
            with patch.object(character_service, "get_character", return_value=test_character):
                # Initialize a new game
                game_state = game_service.initialize_game(
                    character=test_character, scenario_id="goblin-cave-adventure", content_packs=["srd"]
                )

                # Verify game state was created correctly
                assert game_state is not None
                assert game_state.game_id is not None
                assert game_state.scenario_id == "goblin-cave-adventure"
                # Content packs include scenario-specific pack
                assert game_state.content_packs == ["srd", "scenario:goblin-cave-adventure"]

                # Verify character instance was created
                assert game_state.character is not None
                assert isinstance(game_state.character, CharacterInstance)
                assert game_state.character.sheet.name == "Aldric Swiftarrow"
                assert game_state.character.sheet.class_index == "ranger"

                # Verify entity state was initialized
                assert game_state.character.state is not None
                assert isinstance(game_state.character.state, EntityState)
                assert game_state.character.state.level == 3

                # Verify scenario was loaded
                assert game_state.scenario_instance is not None
                assert isinstance(game_state.scenario_instance, ScenarioInstance)

                # Verify initial location is set
                assert game_state.location is not None

                # Save the game
                game_service.save_game(game_state)

                # Verify save file was created
                # Save structure is: saves_dir / scenario_id / game_id / metadata.json
                save_file = self.save_path / "goblin-cave-adventure" / game_state.game_id / "metadata.json"
                assert save_file.exists()

                # Load the saved game
                loaded_game = game_service.load_game(game_state.game_id)

                # Verify loaded game matches original
                assert loaded_game.game_id == game_state.game_id
                assert loaded_game.character.sheet.name == "Aldric Swiftarrow"
                assert loaded_game.scenario_id == "goblin-cave-adventure"

    def test_game_state_persistence(self) -> None:
        """Test that game state changes persist correctly."""
        # Mock the path resolver to use our temp directory and scenario service
        with (
            patch.object(self.container.path_resolver, "saves_dir", self.save_path),
            patch.object(self.container.scenario_service, "get_scenario", side_effect=self.mock_get_scenario),
        ):
            game_service = self.container.game_service

            # Create a minimal test character
            test_character = CharacterSheet(
                id="test-fighter",
                name="Test Fighter",
                race="human",
                class_index="fighter",
                starting_level=1,
                background="soldier",
                alignment="lawful-good",
                personality=Personality(
                    traits=["Brave"],
                    ideals=["Honor"],
                    bonds=["My sword is my life"],
                    flaws=["Too proud"],
                ),
                backstory="A seasoned warrior",
                languages=["common"],
                starting_abilities=Abilities(STR=16, DEX=12, CON=14, INT=10, WIS=12, CHA=8),
                starting_skill_indexes=["athletics"],
                starting_inventory=[],
                starting_currency=Currency(gold=15, silver=0, copper=0),
                starting_experience_points=0,
            )

            # Initialize game
            game_state = game_service.initialize_game(
                character=test_character, scenario_id="test-scenario", content_packs=["srd"]
            )

            original_hp = game_state.character.state.hit_points.current

            # Modify game state
            game_state.character.state.hit_points.current -= 5
            game_state.location = "Deep Forest"
            game_state.combat.is_active = True
            game_state.combat.round_number = 2

            # Save modified state
            game_service.save_game(game_state)

            # Load and verify changes persisted
            loaded_game = game_service.load_game(game_state.game_id)

            assert loaded_game.character.state.hit_points.current == original_hp - 5
            assert loaded_game.location == "Deep Forest"
            assert loaded_game.combat.is_active is True
            assert loaded_game.combat.round_number == 2

    def test_list_saved_games(self) -> None:
        """Test listing saved games."""
        # Mock the path resolver to use our temp directory and scenario service
        with (
            patch.object(self.container.path_resolver, "saves_dir", self.save_path),
            patch.object(self.container.scenario_service, "get_scenario", side_effect=self.mock_get_scenario),
        ):
            game_service = self.container.game_service

            # Initially should be empty
            games = game_service.list_saved_games()
            assert len(games) == 0

            # Create multiple test games
            for i in range(3):
                test_character = CharacterSheet(
                    id=f"test-char-{i}",
                    name=f"Test Character {i}",
                    race="human",
                    class_index="fighter",
                    starting_level=1,
                    background="soldier",
                    alignment="neutral",
                    personality=Personality(
                        traits=["Test"],
                        ideals=["Test"],
                        bonds=["Test"],
                        flaws=["Test"],
                    ),
                    backstory="Test backstory",
                    languages=["common"],
                    starting_abilities=Abilities(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
                    starting_skill_indexes=[],
                    starting_inventory=[],
                    starting_currency=Currency(gold=10, silver=0, copper=0),
                    starting_experience_points=0,
                )

                game_state = game_service.initialize_game(
                    character=test_character, scenario_id=f"scenario-{i}", content_packs=["srd"]
                )
                game_service.save_game(game_state)

            # List games
            games = game_service.list_saved_games()
            assert len(games) == 3

            # Verify each game has required fields
            for game in games:
                assert game.game_id is not None
                assert game.character is not None
                assert game.scenario_id is not None
