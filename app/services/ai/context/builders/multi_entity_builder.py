"""Helper for building context for multiple entities at once."""

from collections.abc import Sequence

from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext
from .inventory_builder import InventoryContextBuilder
from .roleplay_info_builder import RoleplayInfoBuilder
from .spell_builder import SpellContextBuilder


class MultiEntityContextBuilder:
    """Build context for multiple entities (player + party members).

    Coordinates multiple single-entity builders to generate context for
    a collection of entities, avoiding manual loops in the service layer.
    """

    def __init__(
        self,
        roleplay_builder: RoleplayInfoBuilder,
        spell_builder: SpellContextBuilder,
        inventory_builder: InventoryContextBuilder,
    ) -> None:
        """Initialize multi-entity builder.

        Args:
            roleplay_builder: Builder for roleplay info (background, personality, etc.)
            spell_builder: Builder for spell lists
            inventory_builder: Builder for inventories
        """
        self.roleplay_builder = roleplay_builder
        self.spell_builder = spell_builder
        self.inventory_builder = inventory_builder

    def build_party_context(
        self,
        entities: Sequence[CharacterInstance | NPCInstance],
        game_state: GameState,
        context: BuildContext,
        include_roleplay: bool = False,
        include_spells: bool = True,
        include_inventory: bool = True,
    ) -> list[str]:
        """Build context sections for multiple entities.

        Args:
            entities: Sequence of entities to build context for
            game_state: Current game state
            context: Builder dependencies
            include_roleplay: Whether to include roleplay info
            include_spells: Whether to include spell lists
            include_inventory: Whether to include inventories

        Returns:
            List of context strings (already filtered for None)
        """
        parts: list[str] = []

        for entity in entities:
            if include_roleplay:
                part = self.roleplay_builder.build(game_state, context, entity)
                if part:
                    parts.append(part)

            if include_spells:
                part = self.spell_builder.build(game_state, context, entity)
                if part:
                    parts.append(part)

            if include_inventory:
                part = self.inventory_builder.build(game_state, context, entity)
                if part:
                    parts.append(part)

        return parts
