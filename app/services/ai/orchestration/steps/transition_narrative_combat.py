"""Step to handle transition from narrative to combat mode."""

import logging
from datetime import datetime

from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.models.game_state import Message, MessageRole
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class TransitionNarrativeToCombat:
    """Handle the transition from narrative to combat mode.

    This step:
    1. Calls the summarizer agent to create a transition summary
    2. Adds the summary to conversation history as a DM message
    3. Broadcasts the summary to the frontend via event bus

    The transition summary provides combat-relevant context from the narrative
    phase, helping the combat agent understand how the battle started.

    Implementation matches transitions.py lines 27-63.
    """

    def __init__(
        self,
        summarizer_agent: ISummarizerAgent,
        event_bus: IEventBus,
    ):
        """Initialize the step with required services.

        Args:
            summarizer_agent: Agent for generating transition summaries
            event_bus: Event bus for broadcasting to frontend
        """
        self.summarizer_agent = summarizer_agent
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute narrative to combat transition.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult continuing with same context
        """
        logger.info("Transitioning from narrative to combat for game_id=%s", ctx.game_id)

        try:
            # Generate combat transition summary (transitions.py line 30)
            summary = await self.summarizer_agent.summarize_for_combat(ctx.game_state)

            if not summary:
                logger.warning("No summary generated for combat transition")
                return StepResult.continue_with(ctx)

            logger.info("Combat transition summary generated")

            # Add summary to conversation history (transitions.py lines 43-51)
            summary_message = Message(
                role=MessageRole.DM,
                content=f"[Summary: {summary}]",
                timestamp=datetime.now(),
                agent_type=AgentType.COMBAT,
                combat_round=ctx.game_state.combat.round_number if ctx.game_state.combat.is_active else None,
                combat_occurrence=(
                    ctx.game_state.combat.combat_occurrence if ctx.game_state.combat.is_active else None
                ),
            )
            ctx.game_state.conversation_history.append(summary_message)

            # Broadcast summary to frontend (transitions.py lines 54-62)
            await self.event_bus.submit_and_wait(
                [
                    BroadcastNarrativeCommand(
                        game_id=ctx.game_id,
                        content=f"\n*[{summary}]*\n",
                        is_complete=True,
                    )
                ]
            )

            logger.info("Added and broadcast transition summary for combat agent")

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error during narrative to combat transition: %s", exc)

        return StepResult.continue_with(ctx)
