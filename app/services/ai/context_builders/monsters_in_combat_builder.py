from app.models.attributes import EntityType
from app.models.game_state import GameState

from .base import ContextBuilder


class MonstersInCombatContextBuilder(ContextBuilder):
    """List monsters currently participating in combat with stats and initiative."""

    def build(self, game_state: GameState) -> str | None:
        if not game_state.combat.is_active:
            return None

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
