"""Conversation service to record narrative messages (SOLID/DRY)."""

from app.agents.core.types import AgentType
from app.interfaces.services.game import IConversationService, IMessageManager, IMetadataService, ISaveManager
from app.models.game_state import GameState, Message, MessageRole


class ConversationService(IConversationService):
    """Records messages by extracting metadata and persisting immediately."""

    def __init__(
        self,
        message_manager: IMessageManager,
        metadata_service: IMetadataService,
        save_manager: ISaveManager,
    ) -> None:
        self.message_manager = message_manager
        self.metadata_service = metadata_service
        self.save_manager = save_manager

    def record_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType = AgentType.NARRATIVE,
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> Message:
        # Extract metadata when not provided
        if npcs_mentioned is None:
            known_npcs = [npc.sheet.character.name for npc in game_state.npcs]
            npcs_mentioned = self.metadata_service.extract_npcs_mentioned(content, known_npcs)

        if location is None:
            location = self.metadata_service.get_current_location(game_state)

        if combat_round is None and game_state.combat.is_active:
            combat_round = self.metadata_service.get_combat_round(game_state)

        # Add message and persist
        message = self.message_manager.add_message(
            game_state,
            role=role,
            content=content,
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round,
        )
        self.save_manager.save_game(game_state)
        return message
