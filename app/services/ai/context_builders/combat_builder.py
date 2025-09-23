from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class CombatContextBuilder(ContextBuilder):
    """Build detailed combat context, optionally augmented with monster details."""

    def __init__(self, monsters_in_combat_builder: ContextBuilder) -> None:
        self.monsters_in_combat_builder = monsters_in_combat_builder

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.combat.is_active:
            return None

        combat = game_state.combat
        context_parts: list[str] = ["Combat Status:"]

        # Use the built-in turn order display method
        context_parts.append(combat.get_turn_order_display())

        # Add monster details if available
        monsters_block = self.monsters_in_combat_builder.build(game_state, context)
        if monsters_block:
            context_parts.append("\n" + monsters_block)

        return "\n".join(context_parts)
