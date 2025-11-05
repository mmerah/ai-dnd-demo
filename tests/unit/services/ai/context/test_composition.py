"""Tests for ContextComposition and BuilderRegistry."""

from unittest.mock import Mock

from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.context.builders.base import BuildContext, ContextBuilder, EntityContextBuilder
from app.services.ai.context.composition import ContextComposition


class MockGameStateBuilder(ContextBuilder):
    """Mock builder that operates on game state only."""

    def __init__(self, output: str | None):
        self.output = output
        self.call_count = 0

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        self.call_count += 1
        return self.output


class MockEntityBuilder(EntityContextBuilder):
    """Mock builder that operates on entities."""

    def __init__(self, output: str | None):
        self.output = output
        self.call_count = 0
        self.entities_seen: list[CharacterInstance | NPCInstance] = []

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        self.call_count += 1
        self.entities_seen.append(entity)
        return self.output


class TestContextComposition:
    """Test suite for ContextComposition."""

    def test_empty_composition_returns_empty_string(self) -> None:
        """Empty composition should produce empty string."""
        composition = ContextComposition()
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == ""

    def test_single_game_state_builder(self) -> None:
        """Single builder should produce its output."""
        builder = MockGameStateBuilder("Scenario: Test")
        composition = ContextComposition().add(builder)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == "Scenario: Test"
        assert builder.call_count == 1

    def test_multiple_game_state_builders_concatenated(self) -> None:
        """Multiple builders should be concatenated with double newlines."""
        builder1 = MockGameStateBuilder("Part 1")
        builder2 = MockGameStateBuilder("Part 2")
        builder3 = MockGameStateBuilder("Part 3")

        composition = ContextComposition().add(builder1).add(builder2).add(builder3)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == "Part 1\n\nPart 2\n\nPart 3"
        assert builder1.call_count == 1
        assert builder2.call_count == 1
        assert builder3.call_count == 1

    def test_builders_returning_none_are_filtered(self) -> None:
        """Builders that return None should be filtered out."""
        builder1 = MockGameStateBuilder("Part 1")
        builder2 = MockGameStateBuilder(None)  # Returns None
        builder3 = MockGameStateBuilder("Part 3")

        composition = ContextComposition().add(builder1).add(builder2).add(builder3)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == "Part 1\n\nPart 3"
        assert builder2.call_count == 1  # Was called but filtered

    def test_single_entity_builder(self) -> None:
        """Entity builder for single entity works."""
        entity_builder = MockEntityBuilder("Spells: Fireball")
        character = Mock(spec=CharacterInstance)

        composition = ContextComposition().add_for_entity(entity_builder, character)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == "Spells: Fireball"
        assert entity_builder.call_count == 1
        assert entity_builder.entities_seen == [character]

    def test_multi_entity_builder_with_selector(self) -> None:
        """Entity builder with selector applies to all selected entities."""
        entity_builder = MockEntityBuilder("Inventory")
        npc1 = Mock(spec=NPCInstance)
        npc2 = Mock(spec=NPCInstance)
        npc3 = Mock(spec=NPCInstance)

        def selector(gs: GameState) -> list[CharacterInstance | NPCInstance]:
            return [npc1, npc2, npc3]

        composition = ContextComposition().add_for_entities(entity_builder, selector)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        # Should be called 3 times (once per NPC)
        assert result == "Inventory\n\nInventory\n\nInventory"
        assert entity_builder.call_count == 3
        assert entity_builder.entities_seen == [npc1, npc2, npc3]

    def test_multi_entity_builder_with_empty_selector(self) -> None:
        """Entity builder with empty selector produces no output."""
        entity_builder = MockEntityBuilder("Should not appear")

        def empty_selector(gs: GameState) -> list[CharacterInstance | NPCInstance]:
            return []

        composition = ContextComposition().add_for_entities(entity_builder, empty_selector)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == ""
        assert entity_builder.call_count == 0

    def test_mixed_builder_types(self) -> None:
        """Composition with mixed builder types executes in order."""
        game_state_builder = MockGameStateBuilder("Game State")
        entity_builder = MockEntityBuilder("Entity")
        character = Mock(spec=CharacterInstance)
        npc = Mock(spec=NPCInstance)

        composition = (
            ContextComposition()
            .add(game_state_builder)
            .add_for_entity(entity_builder, character)
            .add_for_entities(entity_builder, lambda gs: [npc])
        )
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        # Order: game state builder, single entity, multi-entity
        assert result == "Game State\n\nEntity\n\nEntity"
        assert game_state_builder.call_count == 1
        assert entity_builder.call_count == 2
        assert entity_builder.entities_seen == [character, npc]

    def test_chaining_returns_self(self) -> None:
        """All builder methods should return self for chaining."""
        builder1 = MockGameStateBuilder("A")
        builder2 = MockGameStateBuilder("B")
        entity_builder = MockEntityBuilder("C")
        character = Mock(spec=CharacterInstance)

        composition = ContextComposition()

        # All methods should return the composition instance
        assert composition.add(builder1) is composition
        assert composition.add(builder2) is composition
        assert composition.add_for_entity(entity_builder, character) is composition
        assert composition.add_for_entities(entity_builder, lambda gs: []) is composition

    def test_composition_can_be_executed_multiple_times(self) -> None:
        """Composition should be reusable across multiple builds."""
        builder = MockGameStateBuilder("Output")
        composition = ContextComposition().add(builder)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result1 = composition.build(game_state, build_context)
        result2 = composition.build(game_state, build_context)

        assert result1 == "Output"
        assert result2 == "Output"
        assert builder.call_count == 2  # Called twice

    def test_ordering_preserved(self) -> None:
        """Builders should execute in the order they were added."""
        builder1 = MockGameStateBuilder("First")
        builder2 = MockGameStateBuilder("Second")
        builder3 = MockGameStateBuilder("Third")

        composition = ContextComposition().add(builder1).add(builder2).add(builder3)
        game_state = Mock(spec=GameState)
        build_context = Mock(spec=BuildContext)

        result = composition.build(game_state, build_context)

        assert result == "First\n\nSecond\n\nThird"
