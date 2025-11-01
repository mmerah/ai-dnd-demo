"""Tests for PartyOverviewBuilder."""

from unittest.mock import create_autospec

from app.interfaces.services.data import IRepository
from app.models.background import BackgroundDefinition
from app.models.item import ItemDefinition
from app.models.spell import SpellDefinition
from app.services.ai.context.builders import PartyOverviewBuilder
from app.services.ai.context.builders.base import BuildContext, DetailLevel
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class TestPartyOverviewBuilder:
    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.player_id = self.game_state.character.instance_id
        # Party overview builder doesn't use these repositories, but BuildContext requires them
        self.context = BuildContext(
            item_repository=create_autospec(IRepository[ItemDefinition], instance=True),
            spell_repository=create_autospec(IRepository[SpellDefinition], instance=True),
            background_repository=create_autospec(IRepository[BackgroundDefinition], instance=True),
        )

    def test_full_view_includes_player_id(self) -> None:
        """Test that full view includes player instance ID."""
        builder = PartyOverviewBuilder(detail_level=DetailLevel.FULL)
        result = builder.build(self.game_state, self.context)

        assert result is not None
        assert f"[ID: {self.player_id}]" in result
        assert "Player:" in result

    def test_full_view_includes_party_member_ids(self) -> None:
        """Test that full view includes party member IDs."""
        # Add an NPC to the party
        npc_sheet = make_npc_sheet(npc_id="companion")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="companion-inst")
        self.game_state.npcs.append(npc)
        self.game_state.party.add_member(npc.instance_id)

        builder = PartyOverviewBuilder(detail_level=DetailLevel.FULL)
        result = builder.build(self.game_state, self.context)

        assert result is not None
        assert f"[ID: {npc.instance_id}]" in result
        assert npc.display_name in result

    def test_summary_view_includes_player_id(self) -> None:
        """Test that summary view includes player instance ID."""
        builder = PartyOverviewBuilder(detail_level=DetailLevel.SUMMARY)
        result = builder.build(self.game_state, self.context)

        assert result is not None
        assert f"[ID: {self.player_id}]" in result
        assert "(Player," in result

    def test_summary_view_includes_party_member_ids(self) -> None:
        """Test that summary view includes party member IDs."""
        # Add an NPC to the party
        npc_sheet = make_npc_sheet(npc_id="companion")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="companion-inst")
        self.game_state.npcs.append(npc)
        self.game_state.party.add_member(npc.instance_id)

        builder = PartyOverviewBuilder(detail_level=DetailLevel.SUMMARY)
        result = builder.build(self.game_state, self.context)

        assert result is not None
        assert f"[ID: {npc.instance_id}]" in result
        assert npc.display_name in result
        assert "(Companion," in result
