"""Step to handle transition from combat to narrative mode."""

import logging
from datetime import datetime

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEvent
from app.models.game_state import Message, MessageRole
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class TransitionCombatToNarrative:
    """Handle the transition from combat back to narrative mode.

    This step:
    1. Calls the summarizer agent to create a combat end summary
    2. Adds the summary to conversation history as a DM message
    3. Broadcasts the summary to the frontend
    4. Broadcasts system message about narrative continuation
    5. Prompts the narrative agent with an aftermath prompt
    6. Collects events from narrative agent

    The transition summary provides narrative context about what happened in combat,
    helping the narrative agent continue the story appropriately.

    Implementation matches orchestrator lines 305-334.
    """

    def __init__(
        self,
        summarizer_agent: ISummarizerAgent,
        event_bus: IEventBus,
        context_service: IContextService,
        narrative_agent: BaseAgent,
    ):
        """Initialize the step with required services.

        Args:
            summarizer_agent: Agent for generating transition summaries
            event_bus: Event bus for broadcasting to frontend
            context_service: Service for building agent context
            narrative_agent: Narrative agent for aftermath narration
        """
        self.summarizer_agent = summarizer_agent
        self.event_bus = event_bus
        self.context_service = context_service
        self.narrative_agent = narrative_agent

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute combat to narrative transition.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with events from narrative agent aftermath
        """
        logger.info("Transitioning from combat to narrative for game_id=%s", ctx.game_id)

        try:
            # Generate combat end summary (orchestrator line 314)
            summary = await self.summarizer_agent.summarize_combat_end(ctx.game_state)

            if summary:
                logger.info("Combat end summary generated")

                # Add summary to conversation history (matching transitions.py lines 43-51)
                summary_message = Message(
                    role=MessageRole.DM,
                    content=f"[Summary: {summary}]",
                    timestamp=datetime.now(),
                    agent_type=AgentType.NARRATIVE,
                    combat_round=None,  # Combat has ended
                    combat_occurrence=None,
                )
                ctx.game_state.conversation_history.append(summary_message)

                # Broadcast summary to frontend (matching transitions.py lines 54-62)
                await self.event_bus.submit_and_wait(
                    [
                        BroadcastNarrativeCommand(
                            game_id=ctx.game_id,
                            content=f"\n*[{summary}]*\n",
                            is_complete=True,
                        )
                    ]
                )

                logger.info("Added and broadcast transition summary for narrative agent")

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error during combat to narrative transition summary: %s", exc)

        # Prepare narrative continuation prompt (orchestrator line 319)
        continuation_prompt = "The combat has ended. Describe the aftermath of the battle and continue the narrative."

        # Broadcast system message (orchestrator lines 321-323)
        await self.event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=ctx.game_id,
                    content="[System: Continuing narrative after combat...]",
                    is_complete=True,
                )
            ]
        )

        # Build narrative context and process aftermath (orchestrator lines 330-334)
        narrative_context = self.context_service.build_context(ctx.game_state, AgentType.NARRATIVE)

        events: list[StreamEvent] = []
        async for event in self.narrative_agent.process(
            continuation_prompt,
            ctx.game_state,
            narrative_context,
            stream=True,
        ):
            events.append(event)

        logger.info("Narrative aftermath processed: %d events generated", len(events))

        # Update context with accumulated events
        updated_ctx = ctx.add_events(events)
        return StepResult.continue_with(updated_ctx)
