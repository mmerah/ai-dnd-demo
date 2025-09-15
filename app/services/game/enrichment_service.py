"""Service for enriching game state for display."""

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.data import IRepository, IRepositoryProvider
from app.interfaces.services.game import IGameEnrichmentService
from app.models.game_state import GameState
from app.models.item import InventoryItem, ItemDefinition

logger = logging.getLogger(__name__)


class GameEnrichmentService(IGameEnrichmentService):
    """Handles display enrichment."""

    def __init__(self, repository_provider: IRepositoryProvider):
        """Initialize enrichment service.

        Args:
            repository_provider: Provider for accessing repositories
        """
        self.repository_provider = repository_provider

    def enrich_for_display(self, game_state: GameState) -> GameState:
        item_repo = self.repository_provider.get_item_repository_for(game_state)
        self._enrich_entity_inventory(game_state.character.state.inventory, item_repo)
        for npc in game_state.npcs:
            self._enrich_entity_inventory(npc.state.inventory, item_repo)
        return game_state

    def _enrich_entity_inventory(self, inventory: list[InventoryItem], item_repo: IRepository[ItemDefinition]) -> None:
        """Reusable enrichment logic.

        Args:
            inventory: List of inventory items to enrich
            item_repo: Repository for looking up item definitions
        """
        for item in inventory:
            if not item.name or not item.item_type:
                try:
                    item_def = item_repo.get(item.index)
                    item.name = item_def.name
                    item.item_type = item_def.type
                except RepositoryNotFoundError:
                    # If item not found, create a fallback name
                    if not item.name:
                        item.name = item.index.replace("-", " ").title()
                    logger.warning(f"Item '{item.index}' not found in repository during enrichment")
                except Exception as e:
                    logger.error(f"Error enriching item '{item.index}': {e}")
                    if not item.name:
                        item.name = item.index.replace("-", " ").title()
