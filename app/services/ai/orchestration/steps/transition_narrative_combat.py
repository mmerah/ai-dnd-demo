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
    """Handle the transition from narrative to combat mode."""

    def __init__(
        self,
        summarizer_agent: ISummarizerAgent,
        event_bus: IEventBus,
    ):
        """Initialize with summarizer agent and event bus."""
        self.summarizer_agent = summarizer_agent
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute narrative to combat transition."""
        logger.info("Narrative -> Combat transition")

        try:
            # Generate combat transition summary (transitions.py line 30)
            summary = await self.summarizer_agent.summarize_for_combat(ctx.game_state)

            if not summary:
                logger.warning("No summary generated for combat transition")
                return StepResult.continue_with(ctx)

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

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error during narrative to combat transition: %s", exc)

        return StepResult.continue_with(ctx)
