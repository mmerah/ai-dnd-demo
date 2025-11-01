"""Persona builder for individual NPC prompts."""

from __future__ import annotations

from app.models.instances.npc_instance import NPCInstance


class NPCPersonaContextBuilder:
    """Construct a persona summary for a specific NPC."""

    def build(self, npc: NPCInstance) -> str:
        sheet = npc.sheet
        lines = [
            f"Name: {npc.display_name}",
            f"Role: {sheet.role}",
        ]
        if sheet.description:
            lines.append(f"Description: {sheet.description}")
        attitude = npc.attitude or sheet.initial_attitude
        if attitude:
            lines.append(f"Current attitude toward the party: {attitude}")
        if sheet.initial_notes:
            lines.append("Notable traits: " + "; ".join(sheet.initial_notes))
        if sheet.initial_dialogue_hints:
            lines.append("Dialogue hooks: " + "; ".join(sheet.initial_dialogue_hints))
        return "\n".join(lines)
