"""Integration test for game creation flow."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.container import Container
from app.models.attributes import Abilities
from app.models.character import Currency, Personality
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import DangerLevel
from app.models.scenario import LocationDescriptions, ScenarioAct, ScenarioSheet
from app.models.spell import Spellcasting, SpellcastingAbility, SpellSlot
from tests.factories import make_character_sheet, make_location, make_scenario


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
        goblin_location = make_location(
            location_id="goblin-cave",
            name="Goblin Cave Entrance",
            description="A dark cave entrance looms before you.",
            danger_level=DangerLevel.MODERATE,
            descriptions=LocationDescriptions(
                first_visit="You stand at the entrance of a dark cave.",
                return_visit="The familiar cave entrance awaits.",
            ),
        )

        goblin_act = ScenarioAct(
            id="act1",
            name="Act 1",
            locations=[goblin_location.id],
            objectives=["Explore the cave"],
        )
        goblin_scenario_id = "goblin-cave-adventure"
        self.mock_scenarios[goblin_scenario_id] = make_scenario(
            scenario_id=goblin_scenario_id,
            title="Goblin Cave Adventure",
            description="A classic adventure in a goblin-infested cave.",
            starting_location_id=goblin_location.id,
            locations=[goblin_location],
            acts=[goblin_act],
            content_packs=["srd"],
        )

        # Test scenario for persistence test
        test_location = make_location(
            location_id="test-location",
            name="Test Location",
            description="A test location.",
            danger_level=DangerLevel.SAFE,
        )

        test_act = ScenarioAct(
            id="act1",
            name="Act 1",
            locations=[test_location.id],
            objectives=["Test objective"],
        )
        self.mock_scenarios["test-scenario"] = make_scenario(
            scenario_id="test-scenario",
            title="Test Scenario",
            description="A test scenario.",
            starting_location_id=test_location.id,
            locations=[test_location],
            acts=[test_act],
            content_packs=["srd"],
        )

        # Generic test scenarios for list test
        for i in range(3):
            location_id = f"location-{i}"
            scenario_id = f"scenario-{i}"
            location = make_location(
                location_id=location_id,
                name=f"Location {i}",
                description=f"Location {i} description.",
                danger_level=DangerLevel.SAFE,
            )
            act = ScenarioAct(
                id="act1",
                name="Act 1",
                locations=[location_id],
                objectives=[f"Objective {i}"],
            )

            self.mock_scenarios[scenario_id] = make_scenario(
                scenario_id=scenario_id,
                title=f"Scenario {i}",
                description=f"Test scenario {i}.",
                starting_location_id=location_id,
                locations=[location],
                acts=[act],
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
            ranger_personality = Personality(
                traits=["I am always cautious", "Nature is my friend"],
                ideals=["Balance in all things"],
                bonds=["I must protect the forest"],
                flaws=["I trust too easily"],
            )
            test_character = make_character_sheet(
                character_id="test-ranger",
                name="Aldric Swiftarrow",
                race="wood-elf",
                class_index="ranger",
                starting_level=3,
                background="outlander",
                alignment="neutral-good",
                abilities=Abilities(STR=13, DEX=16, CON=14, INT=12, WIS=15, CHA=10),
                starting_skill_indexes=["survival", "nature"],
                starting_currency=Currency(gold=10, silver=5, copper=20),
                starting_experience_points=900,
                spellcasting=Spellcasting(
                    ability=SpellcastingAbility.WIS,
                    spell_save_dc=13,
                    spell_attack_bonus=5,
                    spells_known=["hunters-mark", "cure-wounds"],
                    spell_slots={
                        1: SpellSlot(level=1, total=3, current=3),
                        2: SpellSlot(level=2, total=0, current=0),
                    },
                ),
                personality=ranger_personality,
                languages=["common", "elvish"],
            )

            # Mock character service to return our test character
            with patch.object(character_service, "get_character", return_value=test_character):
                # Initialize a new game
                goblin_scenario_id = "goblin-cave-adventure"
                game_state = game_service.initialize_game(
                    character=test_character,
                    scenario_id=goblin_scenario_id,
                    content_packs=["srd"],
                )

                # Verify game state was created correctly
                assert game_state is not None
                assert game_state.game_id is not None
                assert game_state.scenario_id == goblin_scenario_id
                expected_packs = ["srd", f"scenario:{goblin_scenario_id}"]
                assert game_state.content_packs == expected_packs

                # Verify character instance was created
                assert game_state.character is not None
                assert isinstance(game_state.character, CharacterInstance)
                assert game_state.character.sheet.name == test_character.name
                assert game_state.character.sheet.class_index == test_character.class_index

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
                save_file = self.save_path / goblin_scenario_id / game_state.game_id / "metadata.json"
                assert save_file.exists()

                # Load the saved game
                loaded_game = game_service.load_game(game_state.game_id)

                # Verify loaded game matches original
                assert loaded_game.game_id == game_state.game_id
                assert loaded_game.character.sheet.name == test_character.name
                assert loaded_game.scenario_id == goblin_scenario_id

    def test_game_state_persistence(self) -> None:
        """Test that game state changes persist correctly."""
        # Mock the path resolver to use our temp directory and scenario service
        with (
            patch.object(self.container.path_resolver, "saves_dir", self.save_path),
            patch.object(self.container.scenario_service, "get_scenario", side_effect=self.mock_get_scenario),
        ):
            game_service = self.container.game_service

            # Create a minimal test character
            fighter_personality = Personality(
                traits=["Brave"],
                ideals=["Honor"],
                bonds=["My sword is my life"],
                flaws=["Too proud"],
            )
            test_character = make_character_sheet(
                character_id="test-fighter",
                name="Test Fighter",
                class_index="fighter",
                starting_level=1,
                abilities=Abilities(STR=16, DEX=12, CON=14, INT=10, WIS=12, CHA=8),
                starting_skill_indexes=["athletics"],
                starting_currency=Currency(gold=15, silver=0, copper=0),
                personality=fighter_personality,
                starting_experience_points=0,
            )

            # Initialize game
            game_state = game_service.initialize_game(
                character=test_character, scenario_id="test-scenario", content_packs=["srd"]
            )

            original_hp = game_state.character.state.hit_points.current

            # Modify game state
            game_state.character.state.hit_points.current -= 5
            new_location_name = "Deep Forest"
            game_state.location = new_location_name
            game_state.combat.is_active = True
            game_state.combat.round_number = 2

            # Save modified state
            game_service.save_game(game_state)

            # Load and verify changes persisted
            loaded_game = game_service.load_game(game_state.game_id)

            assert loaded_game.character.state.hit_points.current == original_hp - 5
            assert loaded_game.location == new_location_name
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
                generic_personality = Personality(
                    traits=["Test"],
                    ideals=["Test"],
                    bonds=["Test"],
                    flaws=["Test"],
                )
                test_character = make_character_sheet(
                    character_id=f"test-char-{i}",
                    name=f"Test Character {i}",
                    class_index="fighter",
                    starting_level=1,
                    alignment="neutral",
                    abilities=Abilities(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
                    starting_currency=Currency(gold=10, silver=0, copper=0),
                    personality=generic_personality,
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
