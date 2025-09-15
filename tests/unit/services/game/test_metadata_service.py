"""Unit tests for MetadataService."""

from unittest.mock import MagicMock, Mock

from app.models.combat import CombatState
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.services.game.metadata_service import MetadataService


class TestMetadataService:
    """Test cases for MetadataService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = MetadataService()

    def _create_mock_character_instance(self) -> CharacterInstance:
        """Create a mock CharacterInstance for testing."""
        character = MagicMock(spec=CharacterInstance)
        character.instance_id = "test-character"
        character.sheet = Mock()
        character.state = Mock()
        return character

    def _create_mock_scenario_instance(self) -> ScenarioInstance:
        """Create a mock ScenarioInstance for testing."""
        scenario = MagicMock(spec=ScenarioInstance)
        scenario.locations = []
        scenario.npcs = []
        scenario.monsters = []
        return scenario

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
        game_state = GameState(
            game_id="test-game",
            character=self._create_mock_character_instance(),
            scenario_id="test-scenario",
            scenario_title="Test Scenario",
            scenario_instance=self._create_mock_scenario_instance(),
            location="Goblin Cave Entrance",
        )
        location = self.service.get_current_location(game_state)
        assert location == "Goblin Cave Entrance"

    def test_get_current_location_default(self) -> None:
        """Test getting location with default value."""
        # Location has a default value of "Unknown"
        game_state = GameState(
            game_id="test-game",
            character=self._create_mock_character_instance(),
            scenario_id="test-scenario",
            scenario_title="Test Scenario",
            scenario_instance=self._create_mock_scenario_instance(),
        )
        location = self.service.get_current_location(game_state)
        assert location == "Unknown"

    def test_get_combat_round_active_combat(self) -> None:
        """Test getting combat round during active combat."""
        combat_state = CombatState(is_active=True, round_number=3)
        game_state = GameState(
            game_id="test-game",
            character=self._create_mock_character_instance(),
            scenario_id="test-scenario",
            scenario_title="Test Scenario",
            scenario_instance=self._create_mock_scenario_instance(),
            combat=combat_state,
        )
        round_num = self.service.get_combat_round(game_state)
        assert round_num == 3

    def test_get_combat_round_inactive_combat(self) -> None:
        """Test getting combat round when combat is inactive."""
        combat_state = CombatState(is_active=False, round_number=1)
        game_state = GameState(
            game_id="test-game",
            character=self._create_mock_character_instance(),
            scenario_id="test-scenario",
            scenario_title="Test Scenario",
            scenario_instance=self._create_mock_scenario_instance(),
            combat=combat_state,
        )
        round_num = self.service.get_combat_round(game_state)
        assert round_num is None

    def test_get_combat_round_multiple_rounds(self) -> None:
        """Test combat round tracking across multiple rounds."""
        for round_number in [1, 5, 10, 99]:
            combat_state = CombatState(is_active=True, round_number=round_number)
            game_state = GameState(
                game_id="test-game",
                character=self._create_mock_character_instance(),
                scenario_id="test-scenario",
                scenario_title="Test Scenario",
                scenario_instance=self._create_mock_scenario_instance(),
                combat=combat_state,
            )
            round_num = self.service.get_combat_round(game_state)
            assert round_num == round_number
