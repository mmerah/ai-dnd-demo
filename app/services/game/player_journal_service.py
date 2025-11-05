"""Player journal service implementation."""

from __future__ import annotations

import logging

from app.interfaces.services.game.player_journal_service import IPlayerJournalService
from app.models.game_state import GameState
from app.models.player_journal import PlayerJournalEntry
from app.utils.id_generator import generate_instance_id

logger = logging.getLogger(__name__)


class PlayerJournalService(IPlayerJournalService):
    """Service for managing player journal entries with auto-linking."""

    def create_entry(
        self,
        game_state: GameState,
        content: str,
        tags: list[str],
    ) -> PlayerJournalEntry:
        # Generate unique entry ID
        entry_id = generate_instance_id("journal-entry")

        # Start with user-provided tags
        auto_tags = list(tags)

        # Auto-link location tag
        location_id = None
        if game_state.scenario_instance.is_in_known_location():
            location_id = game_state.scenario_instance.current_location_id
            location_tag = f"location:{location_id}"
            if location_tag not in auto_tags:
                auto_tags.append(location_tag)
                logger.debug(f"Auto-linked location tag: {location_tag}")

        # Auto-link NPC tags if dialogue session active
        npc_ids = []
        if game_state.dialogue_session.active and game_state.dialogue_session.target_npc_ids:
            npc_ids = game_state.dialogue_session.target_npc_ids.copy()
            for npc_id in npc_ids:
                npc_tag = f"npc:{npc_id}"
                if npc_tag not in auto_tags:
                    auto_tags.append(npc_tag)
                    logger.debug(f"Auto-linked NPC tag: {npc_tag}")

        # Create journal entry
        entry = PlayerJournalEntry(
            entry_id=entry_id,
            content=content,
            tags=auto_tags,
            location_id=location_id,
            npc_ids=npc_ids,
        )

        # Add to game state
        game_state.add_journal_entry(entry)

        logger.info(f"Created journal entry {entry_id} with {len(auto_tags)} tags")
        return entry

    def get_entry(
        self,
        game_state: GameState,
        entry_id: str,
    ) -> PlayerJournalEntry | None:
        return game_state.get_journal_entry(entry_id)

    def list_entries(self, game_state: GameState) -> list[PlayerJournalEntry]:
        return game_state.player_journal_entries

    def update_entry(
        self,
        game_state: GameState,
        entry_id: str,
        content: str,
        tags: list[str],
    ) -> PlayerJournalEntry | None:
        updated_entry = game_state.update_journal_entry(entry_id, content, tags)

        if updated_entry:
            logger.info(f"Updated journal entry {entry_id}")
        else:
            logger.warning(f"Failed to update journal entry {entry_id}: not found")

        return updated_entry

    def delete_entry(
        self,
        game_state: GameState,
        entry_id: str,
    ) -> bool:
        success = game_state.delete_journal_entry(entry_id)

        if success:
            logger.info(f"Deleted journal entry {entry_id}")
        else:
            logger.warning(f"Failed to delete journal entry {entry_id}: not found")

        return success
