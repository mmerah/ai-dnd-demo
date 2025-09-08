"""Minimal character level-up progression service."""

from app.interfaces.services.character import ICharacterComputeService, ILevelProgressionService
from app.models.instances.character_instance import CharacterInstance


class LevelProgressionService(ILevelProgressionService):
    """Provides minimal single-class level-up behavior.

    - Increments level by 1
    - Recomputes derived values via compute service
    - Adjusts current HP by the difference in max HP (clamped)
    - Updates hit dice totals (and clamps current to total)
    """

    def __init__(self, compute_service: ICharacterComputeService) -> None:
        self.compute_service = compute_service

    def level_up_character(self, character: CharacterInstance) -> None:
        state = character.state
        old_max_hp = state.hit_points.maximum

        # Increase level
        state.level += 1

        # Recompute derived values
        new_state = self.compute_service.recompute_entity_state(character.sheet, state)

        # Adjust current HP by the increase in maximum
        hp_delta = max(0, new_state.hit_points.maximum - old_max_hp)
        new_state.hit_points.current = min(new_state.hit_points.maximum, new_state.hit_points.current + hp_delta)

        # Apply updated state
        character.state = new_state
        character.touch()
