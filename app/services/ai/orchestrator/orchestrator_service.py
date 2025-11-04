"""Agent orchestrator to route requests between specialized agents."""

import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import cast

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.agents.npc.base import BaseNPCAgent
from app.agents.tool_suggestor.agent import ToolSuggestorAgent
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService
from app.interfaces.services.game import (
    ICombatService,
    IConversationService,
    IGameService,
    IMetadataService,
)
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.models.game_state import DialogueSessionMode, GameState, MessageRole
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.pipeline import Pipeline
from app.services.ai.orchestration.steps.select_agent import SelectAgent
from app.services.ai.orchestrator import agent_router, combat_loop, state_reload, system_broadcasts, transitions

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinates which agent should handle a given turn by delegating to helpers."""

    def __init__(
        self,
        narrative_agent: BaseAgent,
        combat_agent: BaseAgent,
        summarizer_agent: ISummarizerAgent,
        tool_suggestor_agent: ToolSuggestorAgent,
        context_service: IContextService,
        combat_service: ICombatService,
        event_bus: IEventBus,
        game_service: IGameService,
        metadata_service: IMetadataService,
        conversation_service: IConversationService,
        agent_lifecycle_service: IAgentLifecycleService,
        pipeline: Pipeline | None = None,
    ) -> None:
        self.narrative_agent = narrative_agent
        self.combat_agent = combat_agent
        self.summarizer_agent = summarizer_agent
        self.tool_suggestor_agent = tool_suggestor_agent
        self.context_service = context_service
        self.combat_service = combat_service
        self.event_bus = event_bus
        self.game_service = game_service
        self.metadata_service = metadata_service
        self.conversation_service = conversation_service
        self.agent_lifecycle_service = agent_lifecycle_service
        self.pipeline = pipeline

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process user message with appropriate agent.

        Routes to pipeline if available, otherwise uses legacy path.
        Handles agent selection, transition summaries, and delegation.
        """
        # Route to pipeline if configured
        if self.pipeline is not None:
            async for event in self.process_pipeline(user_message, game_state):
                yield event
            return

        # Legacy path (will be removed in Phase 8)
        # Store whether combat was active before processing
        combat_was_active = game_state.combat.is_active

        if not game_state.combat.is_active:
            targeted_npcs = self._extract_targeted_npcs(user_message, game_state)
            if targeted_npcs:
                async for event in self._handle_npc_dialogue(user_message, game_state, targeted_npcs, stream):
                    yield event
                game_state = state_reload.reload(self.game_service, game_state)
                return
            self._maybe_end_dialogue_session(game_state)
        else:
            current_turn = game_state.combat.get_current_turn()
            if (
                current_turn
                and current_turn.faction == CombatFaction.ALLY
                and current_turn.entity_type == EntityType.NPC
                and not user_message.lstrip().startswith("[ALLY_ACTION]")
            ):
                npc = game_state.get_npc_by_id(current_turn.entity_id)
                if npc is None:
                    raise ValueError(f"Allied NPC {current_turn.entity_id} not found in game state during combat turn")

                if not game_state.party.has_member(npc.instance_id):
                    raise ValueError(
                        f"NPC {npc.display_name} ({npc.instance_id}) has ALLY faction in combat "
                        f"but is not in the party"
                    )

                user_message = (
                    f"[ALLY_ACTION] It is {npc.display_name}'s turn in combat (entity_id={npc.instance_id}, allied NPC). "
                    f"Execute this action exactly as described: {user_message}. "
                    "Use the appropriate combat tools (rolls, damage, HP updates) and CALL next_turn immediately once resolved."
                )

        # Determine current agent type based on game state
        # Phase 1b: Use SelectAgent step to demonstrate pipeline integration
        select_agent_step = SelectAgent()
        orchestration_ctx = OrchestrationContext(
            user_message=user_message,
            game_state=game_state,
        )
        select_result = await select_agent_step.run(orchestration_ctx)
        current_agent_type = select_result.context.require_agent_type()

        # Fallback: verify parity with legacy agent_router
        legacy_agent_type = agent_router.select(game_state)
        if current_agent_type != legacy_agent_type:
            logger.warning(
                "SelectAgent step mismatch: step=%s, legacy=%s",
                current_agent_type,
                legacy_agent_type,
            )

        # Select the appropriate agent
        agent = self.combat_agent if current_agent_type == AgentType.COMBAT else self.narrative_agent

        # Build context for the agent
        context = self.context_service.build_context(game_state, current_agent_type)

        # Get tool suggestions from ToolSuggestorAgent. Does not need context
        tool_suggestions_prompt = f"TARGET_AGENT: {current_agent_type.value}\n\nUSER_PROMPT: {user_message}"
        suggestions_events = [
            event
            async for event in self.tool_suggestor_agent.process(
                tool_suggestions_prompt, game_state, context="", stream=False
            )
        ]

        # Extract suggestions from the complete event
        suggestions = ToolSuggestions(suggestions=[])
        if suggestions_events:
            for event in suggestions_events:
                if event.type == StreamEventType.COMPLETE and isinstance(event.content, ToolSuggestions):
                    suggestions = event.content
                    break

        # Enrich context with suggestions if any
        if suggestions.suggestions:
            suggestions_text = suggestions.format_for_prompt()
            context = f"{context}\n\n{suggestions_text}"

        # Process with selected agent
        async for event in agent.process(user_message, game_state, context, stream=stream):
            yield event

        # Reload game state to get any changes made by handlers during processing
        game_state = state_reload.reload(self.game_service, game_state)
        logger.debug("Reloaded state after agent processing, combat.is_active=%s", game_state.combat.is_active)

        # Check if combat just started (wasn't active before, but is now)
        if not combat_was_active and game_state.combat.is_active:
            async for event in self._handle_combat_start(game_state, stream):
                yield event
            # Reload to check if combat ended
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug("Reloaded state to check combat end, combat.is_active=%s", game_state.combat.is_active)

        # If we're already in combat, check for NPC continuation
        elif game_state.combat.is_active:
            async for event in self._handle_combat_continuation(game_state, stream):
                yield event
            # Reload again to check final combat state
            game_state = state_reload.reload(self.game_service, game_state)
            logger.debug("Reloaded state after combat continuation, combat.is_active=%s", game_state.combat.is_active)

        # Check if combat just ended (was active before, but not now)
        if combat_was_active and not game_state.combat.is_active:
            async for event in self._handle_combat_end(game_state, stream):
                yield event

    def _extract_targeted_npcs(self, user_message: str, game_state: GameState) -> list[str]:
        try:
            return self.metadata_service.extract_targeted_npcs(user_message, game_state)
        except ValueError as exc:
            logger.warning("Failed to resolve targeted NPCs: %s", exc)
            raise

    async def _handle_npc_dialogue(
        self,
        user_message: str,
        game_state: GameState,
        targeted_npc_ids: list[str],
        stream: bool,
    ) -> AsyncIterator[StreamEvent]:
        session = game_state.dialogue_session
        now = datetime.now()
        session.active = True
        session.mode = DialogueSessionMode.EXPLICIT_ONLY
        session.target_npc_ids = targeted_npc_ids
        session.last_interaction_at = now
        if session.started_at is None:
            session.started_at = now

        game_state.active_agent = AgentType.NPC

        self.conversation_service.record_message(
            game_state,
            MessageRole.PLAYER,
            user_message,
            agent_type=AgentType.NPC,
        )

        for npc_id in targeted_npc_ids:
            npc = game_state.get_npc_by_id(npc_id)
            if npc is None:
                raise ValueError(f"NPC with id '{npc_id}' not found")

            agent = cast(BaseNPCAgent, self.agent_lifecycle_service.get_npc_agent(game_state, npc))
            agent.prepare_for_npc(npc)
            # NPC agents build their own context internally (includes persona), so pass empty string
            async for event in agent.process(user_message, game_state, context="", stream=stream):
                yield event
            session.last_interaction_at = datetime.now()

    def _maybe_end_dialogue_session(self, game_state: GameState) -> None:
        session = game_state.dialogue_session
        if session.active and session.mode is DialogueSessionMode.EXPLICIT_ONLY:
            logger.debug("Ending explicit dialogue session for game %s", game_state.game_id)
            session.active = False
            session.target_npc_ids = []
            session.started_at = None
            session.last_interaction_at = None
            game_state.active_agent = AgentType.NARRATIVE

    async def _handle_combat_start(
        self,
        game_state: GameState,
        stream: bool,
    ) -> AsyncIterator[StreamEvent]:
        """Handle the start of combat with transition and initial prompt."""
        logger.info("Combat just started, adding transition context")

        # Transition summary from narrative to combat
        await transitions.handle_transition(
            game_state, AgentType.NARRATIVE, AgentType.COMBAT, self.summarizer_agent, self.event_bus
        )

        # Generate and send initial combat prompt
        initial_prompt = self.combat_service.generate_combat_prompt(game_state)
        current_turn = game_state.combat.get_current_turn()
        is_ally_turn = current_turn is not None and current_turn.faction == CombatFaction.ALLY

        if initial_prompt:
            await system_broadcasts.send_initial_combat_prompt(self.event_bus, game_state.game_id, initial_prompt)

        # Only prompt combat agent immediately if it's not an allied NPC turn
        if not is_ally_turn and initial_prompt:
            combat_context = self.context_service.build_context(game_state, AgentType.COMBAT)
            async for event in self.combat_agent.process(initial_prompt, game_state, combat_context, stream=stream):
                yield event

        # Handle any subsequent NPC/Monster turns or combat ending
        async for event in combat_loop.run(
            game_state=game_state,
            combat_service=self.combat_service,
            combat_agent=self.combat_agent,
            context_service=self.context_service,
            event_bus=self.event_bus,
            agent_lifecycle_service=self.agent_lifecycle_service,
            stream=stream,
        ):
            yield event

    async def _handle_combat_continuation(
        self,
        game_state: GameState,
        stream: bool,
    ) -> AsyncIterator[StreamEvent]:
        """Handle ongoing combat turns for NPCs and monsters."""
        # Reload state to ensure we have the latest combat info
        game_state = state_reload.reload(self.game_service, game_state)
        logger.debug(
            "Reloaded state before combat continuation check, combat.is_active=%s",
            game_state.combat.is_active,
        )

        if not game_state.combat.is_active:
            logger.info("Combat ended during processing, skipping continuation")
            return

        # Run the combat loop to process NPC/monster turns
        async for event in combat_loop.run(
            game_state=game_state,
            combat_service=self.combat_service,
            combat_agent=self.combat_agent,
            context_service=self.context_service,
            event_bus=self.event_bus,
            agent_lifecycle_service=self.agent_lifecycle_service,
            stream=stream,
        ):
            yield event

    async def _handle_combat_end(
        self,
        game_state: GameState,
        stream: bool,
    ) -> AsyncIterator[StreamEvent]:
        """Handle the transition from combat back to narrative."""
        logger.info("Combat just ended, transitioning back to narrative")

        # Transition summary from combat to narrative
        await transitions.handle_transition(
            game_state, AgentType.COMBAT, AgentType.NARRATIVE, self.summarizer_agent, self.event_bus
        )

        # Prepare narrative continuation prompt
        continuation_prompt = "The combat has ended. Describe the aftermath of the battle and continue the narrative."

        await system_broadcasts.send_system_message(
            self.event_bus, game_state.game_id, "Continuing narrative after combat..."
        )

        # Reload state to ensure narrative agent gets the latest
        game_state = state_reload.reload(self.game_service, game_state)
        logger.debug("Reloaded state for narrative aftermath, combat.is_active=%s", game_state.combat.is_active)

        # Process the narrative continuation
        narrative_context = self.context_service.build_context(game_state, AgentType.NARRATIVE)
        async for event in self.narrative_agent.process(
            continuation_prompt, game_state, narrative_context, stream=stream
        ):
            yield event

    async def process_pipeline(
        self,
        user_message: str,
        game_state: GameState,
    ) -> AsyncIterator[StreamEvent]:
        """Process user message using the orchestration pipeline.

        This is the new pipeline-based implementation that replaces the legacy
        monolithic process() method. The pipeline executes a series of composable
        steps with clear separation of concerns.

        Args:
            user_message: Player's message/action to process
            game_state: Current game state

        Yields:
            StreamEvents generated during pipeline execution

        Raises:
            ValueError: If pipeline is not configured
        """
        if self.pipeline is None:
            raise ValueError("Pipeline not configured - cannot use process_pipeline()")

        logger.info(
            "Processing user message via pipeline for game_id=%s",
            game_state.game_id,
        )

        # Create initial orchestration context
        # Capture combat_was_active flag for transition detection
        initial_ctx = OrchestrationContext(
            user_message=user_message,
            game_state=game_state,
            flags=OrchestrationFlags(combat_was_active=game_state.combat.is_active),
        )

        # Execute pipeline and yield all events
        async for event in self.pipeline.execute(initial_ctx):
            yield event

        logger.info(
            "Pipeline execution completed for game_id=%s",
            game_state.game_id,
        )
