"""Build available actions/attacks context for entities."""

import logging

from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, EntityContextBuilder

logger = logging.getLogger(__name__)


class ActionsContextBuilder(EntityContextBuilder):
    """Build available actions/attacks for any entity.

    Shows computed attacks with bonuses, damage, range, and properties.
    Critical for combat agents to understand entity capabilities.
    """

    MAX_ACTIONS = 10

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # Extract entity name based on type
        entity_name = entity.display_name if isinstance(entity, NPCInstance) else entity.sheet.name

        entity_state = entity.state
        if not entity_state.attacks:
            return None

        context_parts = [f"Available Actions ({entity_name}):"]

        for attack in entity_state.attacks[: self.MAX_ACTIONS]:
            # Format: "• Name: +X to hit, damage damage_type, range, [properties]"
            parts = [
                f"  • {attack.name}: +{attack.attack_roll_bonus} to hit",
                f"{attack.damage} {attack.damage_type}",
                attack.range.capitalize(),
            ]

            if attack.reach and attack.reach != "5 ft.":
                parts.append(f"Reach {attack.reach}")

            if attack.properties:
                parts.append(f"[{', '.join(attack.properties)}]")

            if attack.special:
                parts.append(f"({attack.special})")

            context_parts.append(", ".join(parts))

        return "\n".join(context_parts)
