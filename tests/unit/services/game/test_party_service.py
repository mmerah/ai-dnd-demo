"""Unit tests for `PartyService`."""

from __future__ import annotations

import pytest

from app.models.npc import NPCImportance
from app.services.game.party_service import PartyService
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class TestPartyService:
    """Unit tests exercising party management behaviour."""

    def setup_method(self) -> None:
        self.service = PartyService()
        self.game_state = make_game_state()

        # Create a major NPC at the starting location
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

        # Create a minor NPC
        self.minor_npc_sheet = make_npc_sheet(
            npc_id="guard-1",
            display_name="Town Guard",
            role="Guard",
            importance=NPCImportance.MINOR,
        )
        self.minor_npc = make_npc_instance(
            npc_sheet=self.minor_npc_sheet,
            instance_id="npc-guard-1",
            scenario_npc_id="guard-1",
            current_location_id=self.game_state.scenario_instance.current_location_id,
        )
        self.game_state.npcs.append(self.minor_npc)

    def test_add_member_succeeds_for_major_npc_at_same_location(self) -> None:
        self.service.add_member(self.game_state, self.major_npc.instance_id)

        assert self.game_state.party.has_member(self.major_npc.instance_id)
        assert len(self.game_state.party.member_ids) == 1

    def test_add_member_rejects_minor_npc(self) -> None:
        with pytest.raises(ValueError, match="Only major NPCs can join the party"):
            self.service.add_member(self.game_state, self.minor_npc.instance_id)

        assert not self.game_state.party.has_member(self.minor_npc.instance_id)

    def test_add_member_rejects_npc_at_different_location(self) -> None:
        # Move NPC to different location
        self.major_npc.current_location_id = "far-away-location"

        with pytest.raises(ValueError, match="must be at the same location"):
            self.service.add_member(self.game_state, self.major_npc.instance_id)

    def test_add_member_rejects_duplicate(self) -> None:
        self.game_state.party.add_member(self.major_npc.instance_id)

        with pytest.raises(ValueError, match="already in the party"):
            self.service.add_member(self.game_state, self.major_npc.instance_id)

    def test_remove_member_removes_npc_from_party(self) -> None:
        self.game_state.party.add_member(self.major_npc.instance_id)

        self.service.remove_member(self.game_state, self.major_npc.instance_id)

        assert not self.game_state.party.has_member(self.major_npc.instance_id)
        assert len(self.game_state.party.member_ids) == 0

    def test_list_members_returns_npc_instances(self) -> None:
        self.game_state.party.add_member(self.major_npc.instance_id)

        members = self.service.list_members(self.game_state)

        assert len(members) == 1
        assert members[0].instance_id == self.major_npc.instance_id
        assert members[0].display_name == self.major_npc_sheet.display_name

    def test_get_follow_commands_generates_move_commands(self) -> None:
        self.game_state.party.add_member(self.major_npc.instance_id)
        target_location = "new-location"

        commands = self.service.get_follow_commands(self.game_state, target_location)

        assert len(commands) == 1
        assert commands[0].npc_id == self.major_npc.instance_id
        assert commands[0].to_location_id == target_location

    def test_get_follow_commands_skips_npcs_already_at_destination(self) -> None:
        target_location = self.major_npc.current_location_id
        self.game_state.party.add_member(self.major_npc.instance_id)

        commands = self.service.get_follow_commands(self.game_state, target_location)

        assert len(commands) == 0

    def test_is_eligible_returns_true_for_major_npc(self) -> None:
        assert self.service.is_eligible(self.major_npc) is True

    def test_is_eligible_returns_false_for_minor_npc(self) -> None:
        assert self.service.is_eligible(self.minor_npc) is False
