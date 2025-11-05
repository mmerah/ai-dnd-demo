"""Tests for player journal models."""

import time
from datetime import datetime
from typing import Any

import pytest

from app.models.player_journal import PlayerJournalEntry


class TestPlayerJournalEntry:
    """Test PlayerJournalEntry model."""

    def test_basic_journal_entry(self) -> None:
        """Test creating a basic journal entry."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-1234",
            content="Met Tom the barkeep today. He mentioned goblin attacks.",
        )

        assert entry.entry_id == "journal-entry-1234"
        assert entry.content == "Met Tom the barkeep today. He mentioned goblin attacks."
        assert entry.tags == []
        assert entry.location_id is None
        assert entry.npc_ids == []
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)

    def test_entry_with_tags(self) -> None:
        """Test journal entry with manual tags."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-5678",
            content="Remember to buy healing potions before entering the cave.",
            tags=["todo", "preparation", "combat"],
        )

        assert entry.entry_id == "journal-entry-5678"
        assert entry.tags == ["todo", "preparation", "combat"]

    def test_entry_with_location_and_npc_tags(self) -> None:
        """Test journal entry with auto-linked location and NPC tags."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-9012",
            content="Elena agreed to join the party to hunt goblins.",
            tags=["party", "npc:elena-3456", "location:tavern"],
            location_id="tavern",
            npc_ids=["elena-3456"],
        )

        assert entry.location_id == "tavern"
        assert entry.npc_ids == ["elena-3456"]
        assert "npc:elena-3456" in entry.tags
        assert "location:tavern" in entry.tags

    def test_entry_with_multiple_npcs(self) -> None:
        """Test journal entry with multiple NPCs mentioned."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-3333",
            content="Discussed quest with Tom and Elena at the tavern.",
            tags=["location:tavern", "npc:tom-1111", "npc:elena-2222"],
            location_id="tavern",
            npc_ids=["tom-1111", "elena-2222"],
        )

        assert len(entry.npc_ids) == 2
        assert "tom-1111" in entry.npc_ids
        assert "elena-2222" in entry.npc_ids

    def test_touch_updates_timestamp(self) -> None:
        """Test that touch() updates the updated_at timestamp."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-7777",
            content="Original content",
        )

        original_updated_at = entry.updated_at

        # Small delay to ensure timestamp difference
        time.sleep(0.01)

        entry.touch()

        assert entry.updated_at > original_updated_at
        assert entry.created_at == entry.created_at  # created_at should not change

    def test_empty_content_rejected(self) -> None:
        """Test that empty content is rejected."""
        with pytest.raises(ValueError):
            PlayerJournalEntry(
                entry_id="journal-entry-8888",
                content="",
            )

    def test_minimal_required_fields(self) -> None:
        """Test that only entry_id and content are required."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-9999",
            content="Minimal entry",
        )

        assert entry.entry_id == "journal-entry-9999"
        assert entry.content == "Minimal entry"
        assert entry.tags == []
        assert entry.location_id is None
        assert entry.npc_ids == []

    def test_pinned_defaults_to_false(self) -> None:
        """Test that pinned field defaults to False."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-1010",
            content="Test entry",
        )

        assert entry.pinned is False

    def test_entry_can_be_pinned(self) -> None:
        """Test that entry can be created with pinned=True."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-1111",
            content="Important note",
            pinned=True,
        )

        assert entry.pinned is True


class TestPlayerJournalEntryIntegration:
    """Integration tests for PlayerJournalEntry with GameState."""

    def test_entry_serialization(self) -> None:
        """Test that journal entries can be serialized to JSON."""
        entry = PlayerJournalEntry(
            entry_id="journal-entry-4444",
            content="Test entry for serialization",
            tags=["test", "serialization"],
            location_id="test-location",
            npc_ids=["npc-1", "npc-2"],
            pinned=True,
        )

        # Test model_dump (Pydantic v2)
        data = entry.model_dump()

        assert data["entry_id"] == "journal-entry-4444"
        assert data["content"] == "Test entry for serialization"
        assert data["tags"] == ["test", "serialization"]
        assert data["location_id"] == "test-location"
        assert data["npc_ids"] == ["npc-1", "npc-2"]
        assert data["pinned"] is True
        assert "created_at" in data
        assert "updated_at" in data

    def test_entry_deserialization(self) -> None:
        """Test that journal entries can be deserialized from JSON."""
        data: dict[str, Any] = {
            "entry_id": "journal-entry-5555",
            "content": "Test entry for deserialization",
            "tags": ["test", "deserialization"],
            "location_id": "test-location",
            "npc_ids": ["npc-3"],
            "created_at": "2025-11-05T12:00:00",
            "updated_at": "2025-11-05T12:30:00",
            "pinned": True,
        }

        entry = PlayerJournalEntry(**data)

        assert entry.entry_id == "journal-entry-5555"
        assert entry.content == "Test entry for deserialization"
        assert entry.pinned is True
        assert entry.tags == ["test", "deserialization"]
        assert entry.location_id == "test-location"
        assert entry.npc_ids == ["npc-3"]
