"""Unit tests for MetadataService."""

from app.models.combat import CombatState
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.services.game.metadata_service import MetadataService
from tests.factories import make_character_instance, make_character_sheet, make_location, make_scenario


class TestMetadataService:
    """Test cases for MetadataService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = MetadataService()

    def _create_character_instance(self) -> CharacterInstance:
        """Create a CharacterInstance backed by real models."""
        sheet = make_character_sheet()
        return make_character_instance(sheet=sheet, instance_id="test-character")

    def _create_scenario_instance(self) -> ScenarioInstance:
        """Create a ScenarioInstance with default location state."""
        location = make_location(
            location_id="test-location",
            name="Test Location",
            description="A simple test location.",
        )
        scenario = make_scenario(
            scenario_id="test-scenario",
            title="Test Scenario",
            description="A scenario used for metadata tests.",
            starting_location_id=location.id,
            locations=[location],
        )
        scenario_instance = ScenarioInstance(
            instance_id="scenario-instance-1",
            template_id=scenario.id,
            sheet=scenario,
            current_location_id=location.id,
            current_act_id=scenario.progression.acts[0].id,
        )
        scenario_instance.location_states[location.id] = LocationState(location_id=location.id)
        return scenario_instance

    def test_extract_npcs_mentioned_single_npc(self) -> None:
        """Test extracting a single mentioned NPC."""
        content = "I spoke with Barkeep Tom about the goblin raids."
        known_npcs = ["Barkeep Tom", "Elena", "Gruff"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert mentioned == ["Barkeep Tom"]

    def test_extract_npcs_mentioned_multiple_npcs(self) -> None:
        """Test extracting multiple mentioned NPCs."""
        content = "Elena sold me a potion while Gruff watched from the corner."
        known_npcs = ["Barkeep Tom", "Elena", "Gruff", "Marcus"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert set(mentioned) == {"Elena", "Gruff"}
        assert "Barkeep Tom" not in mentioned
        assert "Marcus" not in mentioned

    def test_extract_npcs_mentioned_case_insensitive(self) -> None:
        """Test that NPC extraction is case-insensitive."""
        content = "I met ELENA and spoke with barkeep tom."
        known_npcs = ["Barkeep Tom", "Elena"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert set(mentioned) == {"Barkeep Tom", "Elena"}

    def test_extract_npcs_mentioned_no_duplicates(self) -> None:
        """Test that duplicate mentions are not included."""
        content = "Elena told me about Elena's shop. Elena is nice."
        known_npcs = ["Elena", "Tom"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert mentioned == ["Elena"]
        assert len(mentioned) == 1

    def test_extract_npcs_mentioned_partial_matches(self) -> None:
        """Test that partial name matches work correctly."""
        content = "Tom the barkeep served me a drink."
        known_npcs = ["Tom", "Barkeep Tom", "Elena"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert "Tom" in mentioned

    def test_extract_npcs_mentioned_empty_content(self) -> None:
        """Test with empty content."""
        content = ""
        known_npcs = ["Tom", "Elena"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert mentioned == []

    def test_extract_npcs_mentioned_empty_npcs_list(self) -> None:
        """Test with empty NPC list."""
        content = "I spoke with Tom and Elena."
        known_npcs: list[str] = []
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert mentioned == []

    def test_extract_npcs_mentioned_special_characters(self) -> None:
        """Test with NPCs having special characters in names."""
        content = "I met T'challa and spoke with Anne-Marie."
        known_npcs = ["T'challa", "Anne-Marie", "Bob"]
        mentioned = self.service.extract_npcs_mentioned(content, known_npcs)
        assert set(mentioned) == {"T'challa", "Anne-Marie"}

    def test_get_current_location(self) -> None:
        """Test getting current location from game state."""
        character = self._create_character_instance()
        scenario_instance = self._create_scenario_instance()
        location_label = "Goblin Cave Entrance"
        game_state = GameState(
            game_id="test-game",
            character=character,
            scenario_id=scenario_instance.template_id,
            scenario_title="Test Scenario",
            scenario_instance=scenario_instance,
            location=location_label,
        )
        location = self.service.get_current_location(game_state)
        assert location == location_label

    def test_get_current_location_default(self) -> None:
        """Test getting location with default value."""
        # Location has a default value of "Unknown"
        character = self._create_character_instance()
        scenario_instance = self._create_scenario_instance()
        game_state = GameState(
            game_id="test-game",
            character=character,
            scenario_id=scenario_instance.template_id,
            scenario_title="Test Scenario",
            scenario_instance=scenario_instance,
        )
        location = self.service.get_current_location(game_state)
        assert location == GameState.model_fields["location"].default

    def test_get_combat_round_active_combat(self) -> None:
        """Test getting combat round during active combat."""
        combat_state = CombatState(is_active=True, round_number=3)
        character = self._create_character_instance()
        scenario_instance = self._create_scenario_instance()
        game_state = GameState(
            game_id="test-game",
            character=character,
            scenario_id=scenario_instance.template_id,
            scenario_title="Test Scenario",
            scenario_instance=scenario_instance,
            combat=combat_state,
        )
        round_num = self.service.get_combat_round(game_state)
        assert round_num == 3

    def test_get_combat_round_inactive_combat(self) -> None:
        """Test getting combat round when combat is inactive."""
        combat_state = CombatState(is_active=False, round_number=1)
        character = self._create_character_instance()
        scenario_instance = self._create_scenario_instance()
        game_state = GameState(
            game_id="test-game",
            character=character,
            scenario_id=scenario_instance.template_id,
            scenario_title="Test Scenario",
            scenario_instance=scenario_instance,
            combat=combat_state,
        )
        round_num = self.service.get_combat_round(game_state)
        assert round_num is None

    def test_get_combat_round_multiple_rounds(self) -> None:
        """Test combat round tracking across multiple rounds."""
        for round_number in [1, 5, 10, 99]:
            combat_state = CombatState(is_active=True, round_number=round_number)
            character = self._create_character_instance()
            scenario_instance = self._create_scenario_instance()
            game_state = GameState(
                game_id="test-game",
                character=character,
                scenario_id=scenario_instance.template_id,
                scenario_title="Test Scenario",
                scenario_instance=scenario_instance,
                combat=combat_state,
            )
            round_num = self.service.get_combat_round(game_state)
            assert round_num == round_number
