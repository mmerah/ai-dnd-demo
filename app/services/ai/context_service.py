"""Service for building AI context using composable builders (Strategy pattern)."""

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
        self.builders = [
            LocationContextBuilder(item_repository=self.item_repository),
            NPCsAtLocationContextBuilder(),
            MonstersAtLocationContextBuilder(),
            QuestContextBuilder(),
            CurrentStateContextBuilder(),
            NPCDetailContextBuilder(),
            CombatContextBuilder(monsters_in_combat_builder=monsters_in_combat),
            SpellContextBuilder(spell_repository=self.spell_repository),
            InventoryContextBuilder(),
            NPCItemsContextBuilder(item_repository=self.item_repository),
        ]

    def build_context(self, game_state: GameState) -> str:
        """Build enhanced context string from game state using strategy builders."""
        context_parts: list[str] = []

        # Add scenario header and current location description if available
        if game_state.scenario_instance.is_in_known_location():
            scenario = game_state.scenario_instance.sheet
            location_id = game_state.scenario_instance.current_location_id
            location = scenario.get_location(location_id)
            scenario_context = f"# {scenario.title}\n\n{scenario.description}\n\n"
            if location:
                scenario_context += f"## Current Location: {location.name}\n{location.description}\n\n"
                if location.encounter_ids:
                    scenario_context += f"Potential encounters: {len(location.encounter_ids)} available\n\n"
            context_parts.append(scenario_context)

        # Compose the rest from builders
        for builder in self.builders:
            part = builder.build(game_state)
            if part:
                context_parts.append(part)

        return "\n\n".join(context_parts)
