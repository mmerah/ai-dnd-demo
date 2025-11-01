from app.models.attributes import EntityType
from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class CombatContextBuilder(ContextBuilder):
    """Build detailed combat context including turn order and monster details."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.combat.is_active:
            return None

        combat = game_state.combat
        context_parts: list[str] = ["Combat Status:"]

        # Use the built-in turn order display method
        context_parts.append(combat.get_turn_order_display())

        # Add monster details
        monsters_block = self._build_monsters_in_combat(game_state)
        if monsters_block:
            context_parts.append("\n" + monsters_block)

        return "\n".join(context_parts)

    def _build_monsters_in_combat(self, game_state: GameState) -> str | None:
        """List monsters currently participating in combat with stats and initiative."""
        combat = game_state.combat
        rows: list[str] = []
        for p in combat.participants:
            if p.entity_type != EntityType.MONSTER:
                continue
            monster = game_state.get_entity_by_id(EntityType.MONSTER, p.entity_id)
            if not monster:
                continue
            st = monster.state
            status = "ACTIVE" if p.is_active else "INACTIVE"
            cond = f" [{', '.join(st.conditions)}]" if st.conditions else ""
            rows.append(
                f"  • {p.name} [ID: {p.entity_id}] — Init {p.initiative}, {status}; HP {st.hit_points.current}/{st.hit_points.maximum}, AC {st.armor_class}{cond}"
            )
        if not rows:
            return None
        return "Monsters in Combat:\n" + "\n".join(rows)
