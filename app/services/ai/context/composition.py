"""Declarative composition system for AI context building.

Type-safe, fluent API for configuring which context builders each agent uses.
Mirrors the orchestration Pipeline pattern for consistency.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.context.builders.accumulator import ContextAccumulator
from app.services.ai.context.builders.base import BuildContext, ContextBuilder, EntityContextBuilder
from app.services.ai.context.builders.combat_builder import CombatContextBuilder
from app.services.ai.context.builders.inventory_builder import InventoryContextBuilder
from app.services.ai.context.builders.location_builder import LocationContextBuilder
from app.services.ai.context.builders.location_memory_builder import LocationMemoryContextBuilder
from app.services.ai.context.builders.monsters_location_builder import MonstersAtLocationContextBuilder
from app.services.ai.context.builders.npc_location_builder import NPCLocationContextBuilder
from app.services.ai.context.builders.npc_persona_builder import NPCPersonaContextBuilder
from app.services.ai.context.builders.party_overview_builder import PartyOverviewBuilder
from app.services.ai.context.builders.quest_builder import QuestContextBuilder
from app.services.ai.context.builders.roleplay_info_builder import RoleplayInfoBuilder
from app.services.ai.context.builders.scenario_builder import ScenarioContextBuilder
from app.services.ai.context.builders.spell_builder import SpellContextBuilder
from app.services.ai.context.builders.world_memory_builder import WorldMemoryContextBuilder

# Type alias for entity selector functions
EntitySelector = Callable[[GameState], list[CharacterInstance | NPCInstance]]


@dataclass(frozen=True)
class BuilderRegistry:
    """Immutable registry of all context builder instances.

    Provides named access to builders for composition configuration.
    All builders are initialized once and reused across compositions.
    """

    scenario: ScenarioContextBuilder
    combat: CombatContextBuilder
    party_full: PartyOverviewBuilder
    party_summary: PartyOverviewBuilder
    location: LocationContextBuilder
    location_memory: LocationMemoryContextBuilder
    world_memory: WorldMemoryContextBuilder
    npc_location: NPCLocationContextBuilder
    monsters_location: MonstersAtLocationContextBuilder
    quests: QuestContextBuilder
    spells: SpellContextBuilder
    inventory: InventoryContextBuilder
    roleplay: RoleplayInfoBuilder
    npc_persona: NPCPersonaContextBuilder
    actions: EntityContextBuilder


class ContextComposition:
    """Fluent API for composing context builders.

    Configure which builders execute for an agent type using method chaining.
    Supports game-state builders, single-entity builders, and multi-entity
    builders with selector functions. Reusable across multiple executions.
    """

    def __init__(self) -> None:
        """Initialize an empty composition."""
        self._game_state_builders: list[ContextBuilder] = []
        self._entity_builders: list[tuple[EntityContextBuilder, CharacterInstance | NPCInstance]] = []
        self._multi_entity_builders: list[tuple[EntityContextBuilder, EntitySelector]] = []

    def add(self, builder: ContextBuilder) -> "ContextComposition":
        """Add a game-state builder (operates on GameState only).

        Args:
            builder: ContextBuilder instance (scenario, combat, quests, etc.)

        Returns:
            Self for chaining
        """
        self._game_state_builders.append(builder)
        return self

    def add_for_entity(
        self,
        builder: EntityContextBuilder,
        entity: CharacterInstance | NPCInstance,
    ) -> "ContextComposition":
        """Add entity builder for a single entity.

        Args:
            builder: EntityContextBuilder (spells, inventory, roleplay, etc.)
            entity: Character or NPC instance

        Returns:
            Self for chaining
        """
        self._entity_builders.append((builder, entity))
        return self

    def add_for_entities(
        self,
        builder: EntityContextBuilder,
        selector: EntitySelector,
    ) -> "ContextComposition":
        """Add entity builder for multiple entities via selector function.

        Args:
            builder: EntityContextBuilder to apply to each entity
            selector: Lambda extracting entities from game state

        Returns:
            Self for chaining
        """
        self._multi_entity_builders.append((builder, selector))
        return self

    def build(self, game_state: GameState, context: BuildContext) -> str:
        """Execute all builders and return concatenated context string.

        Executes in order: game-state builders → single-entity → multi-entity.
        Builders returning None are filtered. Sections joined with double newlines.

        Args:
            game_state: Current game state
            context: Builder dependencies (repositories)

        Returns:
            Final context string for agent
        """
        acc = ContextAccumulator()

        # Execute game-state builders
        for game_state_builder in self._game_state_builders:
            acc.add(game_state_builder.build(game_state, context))

        # Execute single-entity builders
        for entity_builder, entity in self._entity_builders:
            acc.add(entity_builder.build(game_state, context, entity))

        # Execute multi-entity builders with selectors
        for entity_builder, selector in self._multi_entity_builders:
            entities = selector(game_state)
            for entity in entities:
                acc.add(entity_builder.build(game_state, context, entity))

        return acc.build()


__all__ = [
    "BuilderRegistry",
    "ContextComposition",
    "EntitySelector",
]
