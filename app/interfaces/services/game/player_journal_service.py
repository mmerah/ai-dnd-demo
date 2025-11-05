"""Interface for player journal service."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.player_journal import PlayerJournalEntry


class IPlayerJournalService(ABC):
    """Service for managing player journal entries with auto-linking and persistence."""

    @abstractmethod
    def create_entry(
        self,
        game_state: GameState,
        content: str,
        tags: list[str],
    ) -> PlayerJournalEntry:
        """Create a new journal entry with auto-linked location and NPC tags.

        Args:
            game_state: Current game state for context (location, dialogue session)
            content: Journal entry text content
            tags: User-provided tags (will be augmented with auto-linked tags)

        Returns:
            The created PlayerJournalEntry with auto-generated ID and timestamps
        """

    @abstractmethod
    def get_entry(
        self,
        game_state: GameState,
        entry_id: str,
    ) -> PlayerJournalEntry | None:
        """Get a specific journal entry by ID.

        Args:
            game_state: Current game state containing journal entries
            entry_id: Unique identifier for the journal entry

        Returns:
            The journal entry if found, None otherwise
        """

    @abstractmethod
    def list_entries(self, game_state: GameState) -> list[PlayerJournalEntry]:
        """List all journal entries for the current game.

        Args:
            game_state: Current game state containing journal entries

        Returns:
            List of all journal entries, ordered by creation time
        """

    @abstractmethod
    def update_entry(
        self,
        game_state: GameState,
        entry_id: str,
        content: str,
        tags: list[str],
        pinned: bool,
    ) -> PlayerJournalEntry | None:
        """Update an existing journal entry's content, tags, and pinned status.

        Args:
            game_state: Current game state containing journal entries
            entry_id: Unique identifier for the journal entry to update
            content: New content for the entry
            tags: New tags for the entry (replaces existing tags)
            pinned: New pinned status for the entry

        Returns:
            The updated journal entry if found, None otherwise
        """

    @abstractmethod
    def delete_entry(
        self,
        game_state: GameState,
        entry_id: str,
    ) -> bool:
        """Delete a journal entry by ID.

        Args:
            game_state: Current game state containing journal entries
            entry_id: Unique identifier for the journal entry to delete

        Returns:
            True if the entry was found and deleted, False if not found
        """
