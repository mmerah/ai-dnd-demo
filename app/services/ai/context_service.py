"""Service for building AI context using composable builders (Strategy pattern)."""

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.interfaces.services.data import IRepositoryProvider
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance

from .context_builders import (
    CombatContextBuilder,
    CurrentStateContextBuilder,
    InventoryContextBuilder,
    LocationContextBuilder,
    LocationMemoryContextBuilder,
    MonstersAtLocationContextBuilder,
    MonstersInCombatContextBuilder,
    NPCDetailContextBuilder,
    NPCItemsContextBuilder,
    NPCMemoryContextBuilder,
    NPCPersonaContextBuilder,
    NPCsAtLocationContextBuilder,
    QuestContextBuilder,
    ScenarioContextBuilder,
    SpellContextBuilder,
    WorldMemoryContextBuilder,
)


class ContextService(IContextService):
    """Coordinator service that composes AI context from multiple builders."""

    def __init__(self, repository_provider: IRepositoryProvider):
        self.repository_provider = repository_provider

        # Instantiate builders with explicit dependencies
        monsters_in_combat = MonstersInCombatContextBuilder()

        # Store individual builders for agent-specific selection
        self.scenario_builder = ScenarioContextBuilder()
        # Builders will receive per-game repositories at build time
        self.location_builder = LocationContextBuilder(item_repository=None)
        self.location_memory_builder = LocationMemoryContextBuilder()
        self.npcs_at_location_builder = NPCsAtLocationContextBuilder()
        self.monsters_at_location_builder = MonstersAtLocationContextBuilder()
        self.quest_builder = QuestContextBuilder()
        self.current_state_builder = CurrentStateContextBuilder()
        self.npc_detail_builder = NPCDetailContextBuilder()
        self.combat_builder = CombatContextBuilder(monsters_in_combat_builder=monsters_in_combat)
        self.monsters_in_combat_builder = monsters_in_combat
        self.spell_builder = SpellContextBuilder(spell_repository=None)
        self.inventory_builder = InventoryContextBuilder()
        self.npc_items_builder = NPCItemsContextBuilder(item_repository=None)
        self.npc_memory_builder = NPCMemoryContextBuilder()
        self.world_memory_builder = WorldMemoryContextBuilder()
        self.npc_persona_builder = NPCPersonaContextBuilder()

        # Full builder list for narrative agent
        self.builders = [
            self.scenario_builder,
            self.location_builder,
            self.location_memory_builder,
            self.npcs_at_location_builder,
            self.monsters_at_location_builder,
            self.quest_builder,
            self.current_state_builder,
            self.npc_detail_builder,
            self.npc_memory_builder,
            self.world_memory_builder,
            self.combat_builder,
            self.spell_builder,
            self.inventory_builder,
            self.npc_items_builder,
        ]

    def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
        # Inject per-game repositories into builders
        item_repo = self.repository_provider.get_item_repository_for(game_state)
        spell_repo = self.repository_provider.get_spell_repository_for(game_state)
        self.location_builder.item_repository = item_repo
        self.spell_builder.spell_repository = spell_repo
        self.npc_items_builder.item_repository = item_repo
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

    def build_context_for_npc(self, game_state: GameState) -> str:
        """NPC-specific slice of the shared game context."""

        item_repo = self.repository_provider.get_item_repository_for(game_state)
        self.location_builder.item_repository = item_repo
        self.npc_items_builder.item_repository = item_repo

        selected_builders = [
            self.scenario_builder,
            self.location_builder,
            self.location_memory_builder,
            self.npcs_at_location_builder,
            self.quest_builder,
            self.current_state_builder,
            self.npc_memory_builder,
            self.world_memory_builder,
            self.inventory_builder,
        ]

        context_parts: list[str] = []
        for builder in selected_builders:
            part = builder.build(game_state)
            if part:
                context_parts.append(part)
        return "\n\n".join(context_parts)

    def build_npc_persona(self, npc: NPCInstance) -> str:
        """Render persona details for a specific NPC."""

        return self.npc_persona_builder.build(npc)
