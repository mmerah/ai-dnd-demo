"""Service for building AI context using composable builders (Strategy pattern)."""

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.interfaces.services.data import IItemRepository, IMonsterRepository, ISpellRepository
from app.models.game_state import GameState

from .context_builders import (
    CombatContextBuilder,
    CurrentStateContextBuilder,
    InventoryContextBuilder,
    LocationContextBuilder,
    MonstersAtLocationContextBuilder,
    MonstersInCombatContextBuilder,
    NPCDetailContextBuilder,
    NPCItemsContextBuilder,
    NPCsAtLocationContextBuilder,
    QuestContextBuilder,
    ScenarioContextBuilder,
    SpellContextBuilder,
)


class ContextService(IContextService):
    """Coordinator service that composes AI context from multiple builders."""

    def __init__(
        self,
        item_repository: IItemRepository,
        monster_repository: IMonsterRepository,
        spell_repository: ISpellRepository,
    ):
        self.item_repository = item_repository
        self.monster_repository = monster_repository
        self.spell_repository = spell_repository

        # Instantiate builders with explicit dependencies
        monsters_in_combat = MonstersInCombatContextBuilder()

        # Store individual builders for agent-specific selection
        self.scenario_builder = ScenarioContextBuilder()
        self.location_builder = LocationContextBuilder(item_repository=self.item_repository)
        self.npcs_at_location_builder = NPCsAtLocationContextBuilder()
        self.monsters_at_location_builder = MonstersAtLocationContextBuilder()
        self.quest_builder = QuestContextBuilder()
        self.current_state_builder = CurrentStateContextBuilder()
        self.npc_detail_builder = NPCDetailContextBuilder()
        self.combat_builder = CombatContextBuilder(monsters_in_combat_builder=monsters_in_combat)
        self.monsters_in_combat_builder = monsters_in_combat
        self.spell_builder = SpellContextBuilder(spell_repository=self.spell_repository)
        self.inventory_builder = InventoryContextBuilder()
        self.npc_items_builder = NPCItemsContextBuilder(item_repository=self.item_repository)

        # Full builder list for narrative agent
        self.builders = [
            self.scenario_builder,
            self.location_builder,
            self.npcs_at_location_builder,
            self.monsters_at_location_builder,
            self.quest_builder,
            self.current_state_builder,
            self.npc_detail_builder,
            self.combat_builder,
            self.spell_builder,
            self.inventory_builder,
            self.npc_items_builder,
        ]

    def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
        """Build enhanced context string from game state using strategy builders.

        Args:
            game_state: Current game state
            agent_type: Type of agent requesting context

        Returns:
            Context string optimized for the specified agent type
        """
        # Select builders based on agent type
        if agent_type == AgentType.COMBAT:
            # Combat agent only needs tactical information
            selected_builders = [
                self.combat_builder,
                self.current_state_builder,
                self.monsters_in_combat_builder,
                self.spell_builder,
                self.inventory_builder,
            ]
        elif agent_type == AgentType.NARRATIVE:
            # Narrative agent needs full context
            selected_builders = self.builders
        elif agent_type == AgentType.SUMMARIZER:
            # Summarizer just needs minimal context
            selected_builders = [
                self.current_state_builder,
                self.combat_builder,
            ]

        context_parts: list[str] = []
        for builder in selected_builders:
            part = builder.build(game_state)
            if part:
                context_parts.append(part)

        return "\n\n".join(context_parts)
