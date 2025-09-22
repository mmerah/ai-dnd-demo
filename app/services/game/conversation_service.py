"""Conversation service to record narrative messages (SOLID/DRY)."""

from datetime import datetime

from app.agents.core.types import AgentType
from app.interfaces.services.game import IConversationService, IMetadataService, ISaveManager
from app.models.game_state import GameState, Message, MessageRole


class ConversationService(IConversationService):
    """Records messages by extracting metadata and persisting immediately."""

    def __init__(
        self,
        metadata_service: IMetadataService,
        save_manager: ISaveManager,
    ) -> None:
        self.metadata_service = metadata_service
        self.save_manager = save_manager

    def record_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType = AgentType.NARRATIVE,
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
    ) -> Message:
        known_npcs = [npc.sheet.character.name for npc in game_state.npcs]
        npcs_mentioned = self.metadata_service.extract_npcs_mentioned(content, known_npcs)

        if role == MessageRole.NPC and speaker_npc_name and speaker_npc_name not in npcs_mentioned:
            npcs_mentioned.append(speaker_npc_name)

        location = self.metadata_service.get_current_location(game_state) or "Unknown"
        combat_round = self.metadata_service.get_combat_round(game_state) or 0
        combat_occurrence = game_state.combat.combat_occurrence if game_state.combat.is_active else None

        # Add message and persist
        message = self.add_message(
            game_state,
            role=role,
            content=content,
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round,
            combat_occurrence=combat_occurrence,
            speaker_npc_id=speaker_npc_id,
            speaker_npc_name=speaker_npc_name,
        )
        self.save_manager.save_game(game_state)
        return message

    def add_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType,
        location: str,
        npcs_mentioned: list[str],
        combat_round: int,
        combat_occurrence: int | None = None,
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
    ) -> Message:
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round if combat_round > 0 else None,
            combat_occurrence=combat_occurrence,
            speaker_npc_id=speaker_npc_id,
            speaker_npc_name=speaker_npc_name,
        )

        game_state.add_message(message)
        return message
