"""Service for building AI context using composable builders (Strategy pattern)."""

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.interfaces.services.data import IRepositoryProvider
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance

from .context_builders import (
    CombatContextBuilder,
    ContextAccumulator,
    DetailLevel,
    InventoryContextBuilder,
    LocationContextBuilder,
    LocationMemoryContextBuilder,
    MonstersAtLocationContextBuilder,
    MonstersInCombatContextBuilder,
    MultiEntityContextBuilder,
    NPCLocationContextBuilder,
    NPCPersonaContextBuilder,
    PartyOverviewBuilder,
    QuestContextBuilder,
    RoleplayInfoBuilder,
    ScenarioContextBuilder,
    SpellContextBuilder,
    WorldMemoryContextBuilder,
)
from .context_builders.base import BuildContext


class ContextService(IContextService):
    """Coordinator service that composes AI context from multiple builders."""

    def __init__(self, repository_provider: IRepositoryProvider):
        self.repository_provider = repository_provider

        # Instantiate builders without repository dependencies
        monsters_in_combat = MonstersInCombatContextBuilder()

        # Store individual builders for agent-specific selection
        self.scenario_builder = ScenarioContextBuilder()
        self.location_builder = LocationContextBuilder()
        self.location_memory_builder = LocationMemoryContextBuilder()
        self.npc_location_builder = NPCLocationContextBuilder()
        self.monsters_at_location_builder = MonstersAtLocationContextBuilder()
        self.quest_builder = QuestContextBuilder()

        # Party overview builders
        self.party_overview_builder_full = PartyOverviewBuilder(detail_level=DetailLevel.FULL)
        self.party_overview_builder_summary = PartyOverviewBuilder(detail_level=DetailLevel.SUMMARY)

        # Entity-aware builders
        self.roleplay_info_builder = RoleplayInfoBuilder()
        self.spell_builder = SpellContextBuilder()
        self.inventory_builder = InventoryContextBuilder()

        # Multi-entity helper for building party-wide context
        self.multi_entity_builder = MultiEntityContextBuilder(
            roleplay_builder=self.roleplay_info_builder,
            spell_builder=self.spell_builder,
            inventory_builder=self.inventory_builder,
        )

        # Other builders
        self.combat_builder = CombatContextBuilder(monsters_in_combat_builder=monsters_in_combat)
        self.monsters_in_combat_builder = monsters_in_combat
        self.world_memory_builder = WorldMemoryContextBuilder()
        self.npc_persona_builder = NPCPersonaContextBuilder()

    def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
        # Create BuildContext with per-game repositories
        item_repo = self.repository_provider.get_item_repository_for(game_state)
        spell_repo = self.repository_provider.get_spell_repository_for(game_state)
        background_repo = self.repository_provider.get_background_repository_for(game_state)
        build_ctx = BuildContext(
            item_repository=item_repo,
            spell_repository=spell_repo,
            background_repository=background_repo,
        )

        acc = ContextAccumulator()
        if agent_type == AgentType.COMBAT:
            self._build_combat_context(acc, game_state, build_ctx)
        elif agent_type == AgentType.NARRATIVE:
            self._build_narrative_context(acc, game_state, build_ctx)
        elif agent_type == AgentType.SUMMARIZER:
            self._build_summarizer_context(acc, game_state, build_ctx)
        return acc.build()

    def _build_combat_context(
        self,
        acc: ContextAccumulator,
        game_state: GameState,
        build_ctx: BuildContext,
    ) -> None:
        """Build combat agent context with party-wide tactical info."""
        # Combat state and turn order
        acc.add(self.combat_builder.build(game_state, build_ctx))
        acc.add(self.party_overview_builder_full.build(game_state, build_ctx))
        acc.add(self.monsters_in_combat_builder.build(game_state, build_ctx))

        # Player character details
        acc.add(self.spell_builder.build(game_state, build_ctx, game_state.character))
        acc.add(self.inventory_builder.build(game_state, build_ctx, game_state.character))

        # Party member details (spells and inventory)
        party_npcs = [game_state.get_npc_by_id(npc_id) for npc_id in game_state.party.member_ids]
        party_npcs_filtered = [npc for npc in party_npcs if npc is not None]
        if party_npcs_filtered:
            party_sections = self.multi_entity_builder.build_party_context(
                entities=party_npcs_filtered,
                game_state=game_state,
                context=build_ctx,
                include_roleplay=False,
                include_spells=True,
                include_inventory=True,
            )
            acc.add_all(party_sections)

    def _build_narrative_context(
        self,
        acc: ContextAccumulator,
        game_state: GameState,
        build_ctx: BuildContext,
    ) -> None:
        """Build narrative agent context with full party details."""
        # Scenario and world
        acc.add(self.scenario_builder.build(game_state, build_ctx))
        acc.add(self.location_builder.build(game_state, build_ctx))
        acc.add(self.location_memory_builder.build(game_state, build_ctx))
        acc.add(self.world_memory_builder.build(game_state, build_ctx))

        # NPCs and monsters at location
        acc.add(self.npc_location_builder.build(game_state, build_ctx))
        acc.add(self.monsters_at_location_builder.build(game_state, build_ctx))

        # Quests
        acc.add(self.quest_builder.build(game_state, build_ctx))

        # Party overview
        acc.add(self.party_overview_builder_full.build(game_state, build_ctx))

        # Player character full details
        acc.add(self.roleplay_info_builder.build(game_state, build_ctx, game_state.character))
        acc.add(self.spell_builder.build(game_state, build_ctx, game_state.character))
        acc.add(self.inventory_builder.build(game_state, build_ctx, game_state.character))

        # Party member full details (roleplay, spells, inventory)
        party_npcs = [game_state.get_npc_by_id(npc_id) for npc_id in game_state.party.member_ids]
        party_npcs_filtered = [npc for npc in party_npcs if npc is not None]
        if party_npcs_filtered:
            party_sections = self.multi_entity_builder.build_party_context(
                entities=party_npcs_filtered,
                game_state=game_state,
                context=build_ctx,
                include_roleplay=True,
                include_spells=True,
                include_inventory=True,
            )
            acc.add_all(party_sections)

    def _build_summarizer_context(
        self,
        acc: ContextAccumulator,
        game_state: GameState,
        build_ctx: BuildContext,
    ) -> None:
        """Build summarizer agent context with minimal information."""
        acc.add(self.party_overview_builder_summary.build(game_state, build_ctx))
        acc.add(self.combat_builder.build(game_state, build_ctx))

    def build_context_for_npc(self, game_state: GameState, npc: NPCInstance) -> str:
        # Create BuildContext with per-game repositories
        item_repo = self.repository_provider.get_item_repository_for(game_state)
        spell_repo = self.repository_provider.get_spell_repository_for(game_state)
        background_repo = self.repository_provider.get_background_repository_for(game_state)
        build_ctx = BuildContext(
            item_repository=item_repo,
            spell_repository=spell_repo,
            background_repository=background_repo,
        )

        acc = ContextAccumulator()

        # Determine if NPC is in the party
        is_party_member = game_state.party.has_member(npc.instance_id)

        # Party overview (full if in party, summary otherwise)
        party_builder = self.party_overview_builder_full if is_party_member else self.party_overview_builder_summary
        acc.add(party_builder.build(game_state, build_ctx))

        # NPC's own details
        acc.add(self.roleplay_info_builder.build(game_state, build_ctx, npc))
        acc.add(self.spell_builder.build(game_state, build_ctx, npc))
        acc.add(self.inventory_builder.build(game_state, build_ctx, npc))

        # Scenario and location context
        acc.add(self.scenario_builder.build(game_state, build_ctx))
        acc.add(self.location_builder.build(game_state, build_ctx))
        acc.add(self.npc_location_builder.build(game_state, build_ctx))
        acc.add(self.quest_builder.build(game_state, build_ctx))

        return acc.build()

    def build_npc_persona(self, npc: NPCInstance) -> str:
        return self.npc_persona_builder.build(npc)
