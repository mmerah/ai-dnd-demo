"""Interface for game enrichment service."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState


class IGameEnrichmentService(ABC):
    """Display enrichment."""

    @abstractmethod
    def enrich_for_display(self, game_state: GameState) -> GameState:
        """Add display names to items for frontend.

        Populates item names from definitions for inventory items that
        only have indexes. This is used when sending game state to frontend.

        Args:
            game_state: The game state to enrich

        Returns:
            The enriched game state (modified in place)
        """
        pass
