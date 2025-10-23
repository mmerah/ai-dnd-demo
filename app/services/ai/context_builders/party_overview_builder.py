"""Builder for party overview context showing player and party members."""

from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder, DetailLevel


class PartyOverviewBuilder(ContextBuilder):
    """Build party overview with player and party members.

    Supports two detail levels:
    - FULL: Complete stats (HP, AC, level, conditions)
    - SUMMARY: Basic info (names and status only)
    """

    def __init__(self, detail_level: DetailLevel = DetailLevel.FULL) -> None:
        self.detail_level = detail_level

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        """Build party overview context.

        Args:
            game_state: Current game state
            context: Builder dependencies

        Returns:
            Party overview string or None if not applicable
        """
        if self.detail_level == DetailLevel.FULL:
            return self._build_full(game_state)
        else:
            return self._build_summary(game_state)

    def _build_full(self, game_state: GameState) -> str:
        """Build full detail party overview."""
        lines = ["Party Overview:"]

        # Player character
        char = game_state.character
        char_sheet = char.sheet
        char_state = char.state
        class_display = char_sheet.class_display

        conditions = f" [{', '.join(char_state.conditions)}]" if char_state.conditions else ""
        player_line = (
            f"• Player: {char_sheet.name} ({char_sheet.race} {class_display} Lvl {char_state.level}) "
            f"— HP {char_state.hit_points.current}/{char_state.hit_points.maximum}, "
            f"AC {char_state.armor_class}{conditions}"
        )
        lines.append(player_line)

        # Party members (major NPCs)
        party_member_ids = game_state.party.member_ids
        if party_member_ids:
            lines.append("\nParty Members:")
            for member_id in party_member_ids:
                npc = game_state.get_npc_by_id(member_id)
                if npc:
                    npc_state = npc.state
                    npc_sheet = npc.sheet.character
                    class_display_npc = npc_sheet.class_display
                    npc_conditions = f" [{', '.join(npc_state.conditions)}]" if npc_state.conditions else ""
                    member_line = (
                        f"• {npc.display_name} ({npc_sheet.race} {class_display_npc} Lvl {npc_state.level}) "
                        f"— HP {npc_state.hit_points.current}/{npc_state.hit_points.maximum}, "
                        f"AC {npc_state.armor_class}{npc_conditions}"
                    )
                    lines.append(member_line)

        # Location and time
        lines.append(f"\nLocation: {game_state.location}")
        lines.append(
            f"Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"
        )

        return "\n".join(lines)

    def _build_summary(self, game_state: GameState) -> str:
        """Build summary detail party overview."""
        lines = ["Party:"]

        # Player
        char_name = game_state.character.sheet.name
        char_hp = game_state.character.state.hit_points
        char_alive = "alive" if char_hp.current > 0 else "unconscious"
        lines.append(f"• {char_name} (Player, {char_alive})")

        # Party members
        party_member_ids = game_state.party.member_ids
        if party_member_ids:
            for member_id in party_member_ids:
                npc = game_state.get_npc_by_id(member_id)
                if npc:
                    npc_hp = npc.state.hit_points
                    npc_alive = "alive" if npc_hp.current > 0 else "unconscious"
                    lines.append(f"• {npc.display_name} (Companion, {npc_alive})")

        return "\n".join(lines)
