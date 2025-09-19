"""Agent orchestrator to route requests between specialized agents."""

import logging
from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.game import ICombatService, IGameService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState
from app.services.ai.orchestrator import agent_router, combat_loop, state_reload, system_broadcasts, transitions

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinates which agent should handle a given turn by delegating to helpers."""

    def __init__(
        self,
        narrative_agent: BaseAgent,
        combat_agent: BaseAgent,
        summarizer_agent: ISummarizerAgent,
        combat_service: ICombatService,
        event_bus: IEventBus,
        game_service: IGameService,
    ) -> None:
        self.narrative_agent = narrative_agent
        self.combat_agent = combat_agent
        self.summarizer_agent = summarizer_agent
        self.combat_service = combat_service
        self.event_bus = event_bus
        self.game_service = game_service

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process user message with appropriate agent.

        Handles agent selection, transition summaries, and delegation.
        """
        # Store whether combat was active before processing
        combat_was_active = game_state.combat.is_active

        # Determine current agent type based on game state
        current_agent_type = agent_router.select(game_state)

        # Select the appropriate agent
        agent = self.combat_agent if current_agent_type == AgentType.COMBAT else self.narrative_agent

        # Process with selected agent
        async for event in agent.process(user_message, game_state, stream=stream):
            yield event

        # Reload game state to get any changes made by handlers during processing
        game_state = state_reload.reload(self.game_service, game_state)
        logger.debug("Reloaded state after agent processing, combat.is_active=%s", game_state.combat.is_active)

        # Check if combat just started (wasn't active before, but is now)
        if not combat_was_active and game_state.combat.is_active:
            logger.info("Combat just started, adding transition context")

            # Transition summary
            await transitions.handle_transition(
                game_state, AgentType.NARRATIVE, AgentType.COMBAT, self.summarizer_agent, self.event_bus
            )

            # Initial combat prompt
            initial_prompt = self.combat_service.generate_combat_prompt(game_state)
            if initial_prompt:
                await system_broadcasts.send_initial_combat_prompt(self.event_bus, game_state.game_id, initial_prompt)
                async for event in self.combat_agent.process(initial_prompt, game_state, stream=stream):
                    yield event

            # Handle any subsequent NPC/Monster turns or combat ending
            async for event in combat_loop.run(
                game_state=game_state,
                combat_service=self.combat_service,
                combat_agent=self.combat_agent,
                event_bus=self.event_bus,
                stream=stream,
            ):
                yield event

            # Reload to check if combat ended
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug("Reloaded state to check combat end, combat.is_active=%s", game_state.combat.is_active)

        # If we're already in combat, check for NPC continuation
        elif game_state.combat.is_active:
            # Reload state again to ensure latest combat info
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug(
                "Reloaded state before combat continuation check, combat.is_active=%s",
                game_state.combat.is_active,
            )

            if not game_state.combat.is_active:
                logger.info("Combat ended during processing, skipping continuation")
                return

            async for event in combat_loop.run(
                game_state=game_state,
                combat_service=self.combat_service,
                combat_agent=self.combat_agent,
                event_bus=self.event_bus,
                stream=stream,
            ):
                yield event

            # Reload again to check final combat state
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug("Reloaded state after combat continuation, combat.is_active=%s", game_state.combat.is_active)

        # Check if combat just ended (was active before, but not now)
        if combat_was_active and not game_state.combat.is_active:
            logger.info("Combat just ended, transitioning back to narrative")

            await transitions.handle_transition(
                game_state, AgentType.COMBAT, AgentType.NARRATIVE, self.summarizer_agent, self.event_bus
            )

            # Prompt narrative continuation
            continuation_prompt = (
                "The combat has ended. Describe the aftermath of the battle and continue the narrative."
            )

            await system_broadcasts.send_system_message(
                self.event_bus, game_state.game_id, "Continuing narrative after combat..."
            )

            # Reload state to ensure narrative agent gets the latest
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug("Reloaded state for narrative aftermath, combat.is_active=%s", game_state.combat.is_active)

            async for event in self.narrative_agent.process(continuation_prompt, game_state, stream=stream):
                yield event
