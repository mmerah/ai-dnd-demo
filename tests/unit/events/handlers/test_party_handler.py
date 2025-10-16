"""Unit tests for PartyHandler."""

from unittest.mock import create_autospec

import pytest

from app.events.commands.party_commands import AddPartyMemberCommand, RemovePartyMemberCommand
from app.events.handlers.party_handler import PartyHandler
from app.interfaces.services.game import IPartyService
from app.models.npc import NPCImportance
from app.models.tool_results import AddPartyMemberResult, RemovePartyMemberResult
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class TestPartyHandler:
    """Test PartyHandler command processing."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.party_service = create_autospec(IPartyService, instance=True)
        self.handler = PartyHandler(self.party_service)
        self.game_state = make_game_state()

        # Create a major NPC
        self.major_npc_sheet = make_npc_sheet(
            npc_id="companion-1",
            display_name="Elara the Wise",
            role="Mage",
            importance=NPCImportance.MAJOR,
        )
        self.major_npc = make_npc_instance(
            npc_sheet=self.major_npc_sheet,
            instance_id="npc-elara-1",
            scenario_npc_id="companion-1",
            current_location_id=self.game_state.scenario_instance.current_location_id,
        )
        self.game_state.npcs.append(self.major_npc)

    @pytest.mark.asyncio
    async def test_add_party_member(self) -> None:
        """Test adding a party member."""
        command = AddPartyMemberCommand(
            game_id=self.game_state.game_id,
            npc_id=self.major_npc.instance_id,
        )

        result = await self.handler.handle(command, self.game_state)

        self.party_service.add_member.assert_called_once_with(self.game_state, self.major_npc.instance_id)

        assert result.mutated
        assert isinstance(result.data, AddPartyMemberResult)
        assert result.data.npc_id == self.major_npc.instance_id
        assert result.data.npc_name == self.major_npc_sheet.display_name

    @pytest.mark.asyncio
    async def test_remove_party_member(self) -> None:
        """Test removing a party member."""
        # Add member first
        self.game_state.party.add_member(self.major_npc.instance_id)

        command = RemovePartyMemberCommand(
            game_id=self.game_state.game_id,
            npc_id=self.major_npc.instance_id,
        )

        result = await self.handler.handle(command, self.game_state)

        self.party_service.remove_member.assert_called_once_with(self.game_state, self.major_npc.instance_id)

        assert result.mutated
        assert isinstance(result.data, RemovePartyMemberResult)
        assert result.data.npc_id == self.major_npc.instance_id
        assert result.data.npc_name == self.major_npc_sheet.display_name

    @pytest.mark.asyncio
    async def test_add_party_member_with_empty_npc_id_error(self) -> None:
        """Test error for empty NPC ID."""
        command = AddPartyMemberCommand(
            game_id=self.game_state.game_id,
            npc_id="",
        )

        with pytest.raises(ValueError, match="NPC ID cannot be empty"):
            await self.handler.handle(command, self.game_state)

    @pytest.mark.asyncio
    async def test_add_party_member_with_invalid_npc_error(self) -> None:
        """Test error for invalid NPC."""
        command = AddPartyMemberCommand(
            game_id=self.game_state.game_id,
            npc_id="non-existent-npc",
        )

        with pytest.raises(ValueError, match="NPC with id"):
            await self.handler.handle(command, self.game_state)

    @pytest.mark.asyncio
    async def test_remove_party_member_with_empty_npc_id_error(self) -> None:
        """Test error for empty NPC ID on remove."""
        command = RemovePartyMemberCommand(
            game_id=self.game_state.game_id,
            npc_id="",
        )

        with pytest.raises(ValueError, match="NPC ID cannot be empty"):
            await self.handler.handle(command, self.game_state)
