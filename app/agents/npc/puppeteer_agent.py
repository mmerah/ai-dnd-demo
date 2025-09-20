"""Shared puppeteer agent for minor NPC portrayals."""

from __future__ import annotations

from pydantic_ai import Agent

from app.agents.core.dependencies import AgentDependencies
from app.agents.core.prompts import PUPPETEER_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.agents.npc.base import BaseNPCAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService, IEventLoggerService, IMessageService
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMessageManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.game_state import GameState, MessageRole
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.debug_logger import AgentDebugLogger
from app.services.ai.message_converter_service import MessageConverterService


class PuppeteerAgent(BaseNPCAgent):
    """Single agent that can embody any minor NPC persona on demand."""

    def __init__(
        self,
        *,
        agent: Agent[AgentDependencies, str],
        context_service: IContextService,
        message_converter: MessageConverterService,
        event_logger: IEventLoggerService,
        metadata_service: IMetadataService,
        event_bus: IEventBus,
        conversation_service: IConversationService,
        scenario_service: IScenarioService,
        repository_provider: IRepositoryProvider,
        message_manager: IMessageManager,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        action_service: IActionService,
        message_service: IMessageService,
        debug_logger: AgentDebugLogger | None = None,
    ) -> None:
        super().__init__(
            agent=agent,
            context_service=context_service,
            message_converter=message_converter,
            event_logger=event_logger,
            metadata_service=metadata_service,
            event_bus=event_bus,
            conversation_service=conversation_service,
            scenario_service=scenario_service,
            repository_provider=repository_provider,
            message_manager=message_manager,
            event_manager=event_manager,
            save_manager=save_manager,
            action_service=action_service,
            message_service=message_service,
            debug_logger=debug_logger,
            system_prompt=PUPPETEER_SYSTEM_PROMPT,
        )

    def _build_context(self, game_state: GameState, npc: NPCInstance) -> str:
        persona = self.context_service.build_npc_persona(npc)
        shared = self.context_service.build_context_for_npc(game_state)
        sections = [
            "Persona Block:\n" + persona,
        ]
        dialogue_session = game_state.dialogue_session
        if dialogue_session.target_npc_ids:
            targeted_names = [
                target.display_name
                for target in game_state.npcs
                if target.instance_id in dialogue_session.target_npc_ids and target.instance_id != npc.instance_id
            ]
            if targeted_names:
                sections.append("Other NPCs expected to respond: " + ", ".join(targeted_names))
        if shared:
            sections.append(shared)
        return "\n\n".join(section for section in sections if section)

    def _build_prompt(
        self,
        player_message: str,
        npc: NPCInstance,
        game_state: GameState,
        context_text: str,
    ) -> str:
        dialogue_history = self._summarize_recent_dialogue(game_state, npc)
        parts = [context_text]
        if dialogue_history:
            parts.append("Recent exchange:\n" + dialogue_history)
        parts.append(
            "Guidelines:\n"
            "- Reply in first person as the NPC described in the persona block.\n"
            "- Keep the response focused (no more than 4 sentences).\n"
            "- Only reveal knowledge the NPC plausibly has."
        )
        parts.append(f"Player message: {player_message}")
        return "\n\n".join(part for part in parts if part)

    def _summarize_recent_dialogue(self, game_state: GameState, npc: NPCInstance, limit: int = 4) -> str:
        history: list[str] = []
        for message in reversed(game_state.conversation_history):
            if len(history) >= limit:
                break
            if message.role == MessageRole.PLAYER and message.agent_type == AgentType.NPC:
                history.append(f"Player: {message.content}")
            elif message.role == MessageRole.NPC and message.speaker_npc_id == npc.instance_id:
                history.append(f"{npc.display_name}: {message.content}")
        history.reverse()
        return "\n".join(history)
