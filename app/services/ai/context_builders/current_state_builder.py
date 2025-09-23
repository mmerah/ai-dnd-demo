from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class CurrentStateContextBuilder(ContextBuilder):
    """Build the player's current state summary."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        char_sheet = game_state.character.sheet
        char_state = game_state.character.state
        char_instance = game_state.character
        class_display = char_sheet.class_display
        return f"""Current State:\n- Character: {char_sheet.name} (ID: {char_instance.instance_id}) ({char_sheet.race} {class_display} Level {char_state.level})\n- HP: {char_state.hit_points.current}/{char_state.hit_points.maximum}, AC: {char_state.armor_class}\n- Location: {game_state.location}\n- Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"""
