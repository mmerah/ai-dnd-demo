from app.models.game_state import GameState

from .base import ContextBuilder


class CombatContextBuilder(ContextBuilder):
    """Build detailed combat context, optionally augmented with monster details."""

    def __init__(self, monsters_in_combat_builder: ContextBuilder) -> None:
        self.monsters_in_combat_builder = monsters_in_combat_builder

    def build(self, game_state: GameState) -> str | None:
        if not game_state.combat:
            return None

        combat = game_state.combat
        current_turn = combat.get_current_turn()
        context_parts: list[str] = [f"Combat Status - Round {combat.round_number}:"]

        if current_turn:
            context_parts.append(f"Current Turn: {current_turn.name}")

        context_parts.append("\nInitiative Order:")
        for participant in combat.participants:
            if participant.is_active:
                marker = "→" if current_turn and participant.name == current_turn.name else " "
                player_tag = " [PLAYER]" if participant.is_player else ""
                context_parts.append(
                    f"  {marker} {participant.initiative:2d}: {participant.name}{player_tag} (ID: {participant.entity_id})"
                )

        monsters_block = self.monsters_in_combat_builder.build(game_state)
        if monsters_block:
            context_parts.append("\n" + monsters_block)

        return "\n".join(context_parts)
