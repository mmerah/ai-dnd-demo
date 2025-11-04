"""Service for building AI context using composable builders (Strategy pattern)."""

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.interfaces.services.data import IRepositoryProvider
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.context.builders import (
    ActionsContextBuilder,
    CombatContextBuilder,
    DetailLevel,
    InventoryContextBuilder,
    LocationContextBuilder,
    LocationMemoryContextBuilder,
    MonstersAtLocationContextBuilder,
    NPCLocationContextBuilder,
    NPCPersonaContextBuilder,
    PartyOverviewBuilder,
    QuestContextBuilder,
    RoleplayInfoBuilder,
    ScenarioContextBuilder,
    SpellContextBuilder,
    WorldMemoryContextBuilder,
)
from app.services.ai.context.builders.base import BuildContext
from app.services.ai.context.composition import BuilderRegistry, ContextComposition


class ContextService(IContextService):
    """Coordinator service that composes AI context from multiple builders.

    Uses declarative composition pattern to configure context for each agent type.
    Each agent type has an explicit, self-documenting composition that specifies
    which builders to use and in what order.
    """

    def __init__(self, repository_provider: IRepositoryProvider):
        self.repository_provider = repository_provider

        # Initialize all builders once
        self._builders = self._create_builders()

        # Create explicit, declarative compositions for each agent type
        self._compositions = self._create_compositions()

    def _create_builders(self) -> BuilderRegistry:
        """Initialize all available context builders.

        Returns:
            BuilderRegistry with all builder instances
        """
        return BuilderRegistry(
            scenario=ScenarioContextBuilder(),
            combat=CombatContextBuilder(),
            party_full=PartyOverviewBuilder(detail_level=DetailLevel.FULL),
            party_summary=PartyOverviewBuilder(detail_level=DetailLevel.SUMMARY),
            location=LocationContextBuilder(),
            location_memory=LocationMemoryContextBuilder(),
            world_memory=WorldMemoryContextBuilder(),
            npc_location=NPCLocationContextBuilder(),
            monsters_location=MonstersAtLocationContextBuilder(),
            quests=QuestContextBuilder(),
            spells=SpellContextBuilder(),
            inventory=InventoryContextBuilder(),
            roleplay=RoleplayInfoBuilder(),
            npc_persona=NPCPersonaContextBuilder(),
            actions=ActionsContextBuilder(),
        )

    def _create_compositions(self) -> dict[AgentType, ContextComposition]:
        """Create explicit context configurations for each agent type.

        This method provides a declarative, self-documenting view of what context
        each agent receives. To modify an agent's context, simply add/remove/reorder
        builders in the appropriate composition.

        Returns:
            Dictionary mapping agent types to their context compositions
        """
        b = self._builders

        return {
            # NARRATIVE: Full story context with world state, quests, and all party details
            AgentType.NARRATIVE: (
                ContextComposition()
                # World and scenario context
                .add(b.scenario)
                .add(b.location)
                .add(b.location_memory)
                .add(b.world_memory)
                # NPCs and monsters at location
                .add(b.npc_location)
                .add(b.monsters_location)
                # Quests
                .add(b.quests)
                # Party overview
                .add(b.party_full)
                # Player character details
                .add_for_entities(b.roleplay, lambda gs: [gs.character])
                .add_for_entities(b.spells, lambda gs: [gs.character])
                .add_for_entities(b.inventory, lambda gs: [gs.character])
                # Party member details (roleplay, spells, inventory)
                .add_for_entities(b.roleplay, self._get_party_members)
                .add_for_entities(b.spells, self._get_party_members)
                .add_for_entities(b.inventory, self._get_party_members)
            ),
            # COMBAT: Tactical context with combat state and character abilities
            AgentType.COMBAT: (
                ContextComposition()
                # Combat state and turn order
                .add(b.combat)
                .add(b.party_full)
                # Player character abilities
                .add_for_entities(b.actions, lambda gs: [gs.character])
                .add_for_entities(b.spells, lambda gs: [gs.character])
                .add_for_entities(b.inventory, lambda gs: [gs.character])
                # Party member abilities (actions, spells, inventory)
                .add_for_entities(b.actions, self._get_party_members)
                .add_for_entities(b.spells, self._get_party_members)
                .add_for_entities(b.inventory, self._get_party_members)
            ),
            # SUMMARIZER: Minimal context for summarization tasks
            AgentType.SUMMARIZER: (ContextComposition().add(b.party_summary).add(b.combat)),
        }

    def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
        build_ctx = self._create_build_context(game_state)
        composition = self._compositions[agent_type]
        return composition.build(game_state, build_ctx)

    def build_context_for_npc(self, game_state: GameState, npc: NPCInstance) -> str:
        build_ctx = self._create_build_context(game_state)
        b = self._builders

        # Determine party detail level based on membership
        is_party_member = game_state.party.has_member(npc.instance_id)
        party_builder = b.party_full if is_party_member else b.party_summary

        # Build NPC-specific composition
        composition = (
            ContextComposition()
            # Party overview (full if in party, summary otherwise)
            .add(party_builder)
            # Combat context (turn order, initiative, combat state)
            .add(b.combat)
            # NPC's own details
            .add_for_entity(b.roleplay, npc)
            .add_for_entity(b.actions, npc)
            .add_for_entity(b.spells, npc)
            .add_for_entity(b.inventory, npc)
            # World and scenario context
            .add(b.scenario)
            .add(b.location)
            .add(b.location_memory)
            .add(b.world_memory)
            # NPCs and monsters at location
            .add(b.npc_location)
            .add(b.monsters_location)
            # Quests
            .add(b.quests)
        )

        return composition.build(game_state, build_ctx)

    def build_npc_persona(self, npc: NPCInstance) -> str:
        """Build persona description for a specific NPC.

        Args:
            npc: The NPC instance

        Returns:
            Persona description string
        """
        return self._builders.npc_persona.build(npc)

    def _create_build_context(self, game_state: GameState) -> BuildContext:
        """Create BuildContext with per-game repositories.

        Args:
            game_state: Current game state

        Returns:
            BuildContext with repositories for this game
        """
        return BuildContext(
            item_repository=self.repository_provider.get_item_repository_for(game_state),
            spell_repository=self.repository_provider.get_spell_repository_for(game_state),
            background_repository=self.repository_provider.get_background_repository_for(game_state),
        )

    @staticmethod
    def _get_party_members(game_state: GameState) -> list[NPCInstance | CharacterInstance]:
        """Extract party members from game state.

        Args:
            game_state: Current game state

        Returns:
            List of NPC instances that are party members (returns union type for compatibility)
        """
        party_npcs: list[NPCInstance | CharacterInstance] = []
        for npc_id in game_state.party.member_ids:
            npc = game_state.get_npc_by_id(npc_id)
            if npc is not None:
                party_npcs.append(npc)
        return party_npcs
