"""Service for building AI context following Single Responsibility."""

from app.models.game_state import GameState
from app.services.scenario_service import ScenarioService


class ContextService:
    """Service for building AI context following Single Responsibility."""

    def __init__(self, scenario_service: ScenarioService):
        self.scenario_service = scenario_service

    def build_context(self, game_state: GameState) -> str:
        """Build context string from game state."""
        context_parts = []

        # Add scenario context if available
        if game_state.scenario_id and game_state.current_location_id:
            scenario = self.scenario_service.get_scenario(game_state.scenario_id)
            if scenario:
                scenario_context = self.scenario_service.get_scenario_context_for_ai(
                    scenario, game_state.current_location_id
                )
                context_parts.append(scenario_context)

        # Add current game state
        char = game_state.character
        context_parts.append(
            f"""Current State:
- Character: {char.name} ({char.race} {char.class_name} Level {char.level})
- HP: {char.hit_points.current}/{char.hit_points.maximum}, AC: {char.armor_class}
- Location: {game_state.location}
- Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"""
        )

        if game_state.npcs:
            npc_lines = [
                f"  - {npc.name}: HP {npc.hit_points.current}/{npc.hit_points.maximum}, AC {npc.armor_class}"
                for npc in game_state.npcs
            ]
            context_parts.append("NPCs Present:\n" + "\n".join(npc_lines))

        if game_state.combat:
            current_turn = game_state.combat.get_current_turn()
            turn_info = f", Turn: {current_turn.name}" if current_turn else ""
            context_parts.append(f"Combat: Round {game_state.combat.round_number}{turn_info}")

        return "\n\n".join(context_parts)
