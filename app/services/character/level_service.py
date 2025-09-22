"""Minimal entity level-up progression service."""

from app.interfaces.services.character import ICharacterComputeService, ILevelProgressionService
from app.models.game_state import GameState
from app.utils.entity_resolver import resolve_entity_with_fallback


class LevelProgressionService(ILevelProgressionService):
    """Provides minimal single-class level-up behavior for entities."""

    def __init__(self, compute_service: ICharacterComputeService) -> None:
        self.compute_service = compute_service

    def level_up_entity(self, game_state: GameState, entity_id: str) -> None:
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        state = entity.state
        old_max_hp = state.hit_points.maximum

        # Increase level
        state.level += 1

        # For player character, use the character sheet
        if entity.instance_id == game_state.character.instance_id:
            character = game_state.character
            new_state = self.compute_service.recompute_entity_state(game_state, character.sheet, state)

            # Adjust current HP by the increase in maximum
            hp_delta = max(0, new_state.hit_points.maximum - old_max_hp)
            new_state.hit_points.current = min(new_state.hit_points.maximum, new_state.hit_points.current + hp_delta)

            # Apply updated state
            character.state = new_state
            character.touch()
        else:
            # For NPCs, use the NPC's character sheet from NPCSheet
            npc = next((n for n in game_state.npcs if n.instance_id == entity_id), None)
            if npc:
                new_state = self.compute_service.recompute_entity_state(game_state, npc.sheet.character, state)

                # Adjust current HP by the increase in maximum
                hp_delta = max(0, new_state.hit_points.maximum - old_max_hp)
                new_state.hit_points.current = min(
                    new_state.hit_points.maximum, new_state.hit_points.current + hp_delta
                )

                # Apply updated state
                npc.state = new_state
            else:
                # Monsters typically don't level up, but if needed, just increase level and HP
                state.hit_points.maximum += 5
                state.hit_points.current = min(state.hit_points.maximum, state.hit_points.current + 5)
