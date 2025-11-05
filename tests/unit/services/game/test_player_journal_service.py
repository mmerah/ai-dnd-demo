"""Tests for PlayerJournalService."""

from app.services.game.player_journal_service import PlayerJournalService
from tests.factories.game_state import make_game_state


class TestPlayerJournalService:
    """Test PlayerJournalService business logic."""

    def test_create_entry_basic(self) -> None:
        """Test creating a basic journal entry with auto-linking."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Test entry content", ["tag1", "tag2"])

        assert entry.content == "Test entry content"
        assert "tag1" in entry.tags
        assert "tag2" in entry.tags
        # make_game_state() starts with a location by default
        assert entry.location_id is not None
        assert len(entry.npc_ids) == 0
        assert len(game_state.player_journal_entries) == 1

    def test_create_entry_auto_links_location_when_known(self) -> None:
        """Test that location is auto-linked when in a known location."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "tavern-123"
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Met the barkeep", [])

        assert "location:tavern-123" in entry.tags
        assert entry.location_id == "tavern-123"

    def test_create_entry_no_location_when_unknown(self) -> None:
        """Test that location is not auto-linked when in unknown location."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "unknown-location"
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Wandering in the wilderness", [])

        assert entry.location_id is None
        assert not any(tag.startswith("location:") for tag in entry.tags)

    def test_create_entry_auto_links_npc_when_dialogue_active(self) -> None:
        """Test that NPC is auto-linked when dialogue session is active."""
        game_state = make_game_state()
        game_state.dialogue_session.active = True
        game_state.dialogue_session.target_npc_ids = ["elena-456"]
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Elena agreed to help", [])

        assert "npc:elena-456" in entry.tags
        assert "elena-456" in entry.npc_ids

    def test_create_entry_auto_links_multiple_npcs(self) -> None:
        """Test that multiple NPCs are auto-linked during group dialogue."""
        game_state = make_game_state()
        game_state.dialogue_session.active = True
        game_state.dialogue_session.target_npc_ids = ["guard-1", "guard-2"]
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Spoke with the guards", [])

        assert "npc:guard-1" in entry.tags
        assert "npc:guard-2" in entry.tags
        assert "guard-1" in entry.npc_ids
        assert "guard-2" in entry.npc_ids

    def test_create_entry_no_npc_when_dialogue_inactive(self) -> None:
        """Test that NPCs are not auto-linked when dialogue is inactive."""
        game_state = make_game_state()
        game_state.dialogue_session.active = False
        game_state.dialogue_session.target_npc_ids = ["elena-456"]
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Left the tavern", [])

        assert len(entry.npc_ids) == 0
        assert not any(tag.startswith("npc:") for tag in entry.tags)

    def test_create_entry_preserves_user_tags(self) -> None:
        """Test that user-provided tags are preserved alongside auto-linked tags."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "cave-789"
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Important note", ["todo", "urgent"])

        assert "todo" in entry.tags
        assert "urgent" in entry.tags
        assert "location:cave-789" in entry.tags

    def test_create_entry_does_not_duplicate_tags(self) -> None:
        """Test that auto-linking doesn't duplicate manually provided tags."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "tavern-123"
        service = PlayerJournalService()

        # User manually adds location tag
        entry = service.create_entry(game_state, "Test", ["location:tavern-123"])

        # Should only appear once
        assert entry.tags.count("location:tavern-123") == 1

    def test_create_entry_auto_links_both_location_and_npc(self) -> None:
        """Test that both location and NPC are auto-linked when available."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "inn-999"
        game_state.dialogue_session.active = True
        game_state.dialogue_session.target_npc_ids = ["innkeeper-555"]
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Rented a room", ["payment"])

        assert "location:inn-999" in entry.tags
        assert "npc:innkeeper-555" in entry.tags
        assert "payment" in entry.tags
        assert entry.location_id == "inn-999"
        assert "innkeeper-555" in entry.npc_ids

    def test_get_entry_returns_none_when_not_found(self) -> None:
        """Test that get_entry returns None for non-existent entry."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry = service.get_entry(game_state, "non-existent-id")

        assert entry is None

    def test_get_entry_returns_entry_when_found(self) -> None:
        """Test that get_entry returns the correct entry."""
        game_state = make_game_state()
        service = PlayerJournalService()

        created_entry = service.create_entry(game_state, "Test", [])
        retrieved_entry = service.get_entry(game_state, created_entry.entry_id)

        assert retrieved_entry is not None
        assert retrieved_entry.entry_id == created_entry.entry_id
        assert retrieved_entry.content == "Test"

    def test_list_entries_returns_all_entries(self) -> None:
        """Test that list_entries returns all journal entries."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry1 = service.create_entry(game_state, "First", [])
        entry2 = service.create_entry(game_state, "Second", [])
        entry3 = service.create_entry(game_state, "Third", [])

        entries = service.list_entries(game_state)

        assert len(entries) == 3
        assert entries[0].entry_id == entry1.entry_id
        assert entries[1].entry_id == entry2.entry_id
        assert entries[2].entry_id == entry3.entry_id

    def test_list_entries_returns_empty_for_new_game(self) -> None:
        """Test that list_entries returns empty list for new game."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entries = service.list_entries(game_state)

        assert len(entries) == 0

    def test_update_entry_modifies_content_and_tags(self) -> None:
        """Test that update_entry changes content and tags."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Original", ["old-tag"])
        updated = service.update_entry(game_state, entry.entry_id, "Updated", ["new-tag"])

        assert updated is not None
        assert updated.content == "Updated"
        assert updated.tags == ["new-tag"]

    def test_update_entry_does_not_modify_auto_linked_ids(self) -> None:
        """Test that update preserves location_id and npc_ids from creation."""
        game_state = make_game_state()
        game_state.scenario_instance.current_location_id = "cave-123"
        game_state.dialogue_session.active = True
        game_state.dialogue_session.target_npc_ids = ["npc-456"]
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Original", [])
        original_location_id = entry.location_id
        original_npc_ids = entry.npc_ids.copy()

        # Move to different location and deactivate dialogue
        game_state.scenario_instance.current_location_id = "different-location"
        game_state.dialogue_session.active = False

        updated = service.update_entry(game_state, entry.entry_id, "Updated", ["new-tag"])

        # Auto-linked IDs should remain unchanged
        assert updated is not None
        assert updated.location_id == original_location_id
        assert updated.npc_ids == original_npc_ids

    def test_update_entry_updates_timestamp(self) -> None:
        """Test that update_entry updates the timestamp."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Original", [])
        original_updated_at = entry.updated_at

        import time

        time.sleep(0.01)

        updated = service.update_entry(game_state, entry.entry_id, "Updated", [])

        assert updated is not None
        assert updated.updated_at > original_updated_at

    def test_update_entry_returns_none_when_not_found(self) -> None:
        """Test that update_entry returns None for non-existent entry."""
        game_state = make_game_state()
        service = PlayerJournalService()

        updated = service.update_entry(game_state, "non-existent", "New content", [])

        assert updated is None

    def test_delete_entry_removes_entry(self) -> None:
        """Test that delete_entry removes the entry."""
        game_state = make_game_state()
        service = PlayerJournalService()

        entry = service.create_entry(game_state, "Test", [])
        success = service.delete_entry(game_state, entry.entry_id)

        assert success is True
        assert len(game_state.player_journal_entries) == 0

    def test_delete_entry_returns_false_when_not_found(self) -> None:
        """Test that delete_entry returns False for non-existent entry."""
        game_state = make_game_state()
        service = PlayerJournalService()

        success = service.delete_entry(game_state, "non-existent")

        assert success is False
