"""Standardized system/auto messages for broadcasts."""

from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus


async def send_system_message(event_bus: IEventBus, game_id: str, message: str) -> None:
    """Broadcast a simple system message to the chat."""
    await event_bus.submit_and_wait(
        [BroadcastNarrativeCommand(game_id=game_id, content=f"[System: {message}]", is_complete=True)]
    )


async def send_auto_combat_prompt(event_bus: IEventBus, game_id: str, prompt: str) -> None:
    """Broadcast an auto-combat prompt text for visibility in chat."""
    await event_bus.submit_and_wait(
        [BroadcastNarrativeCommand(game_id=game_id, content=f"[Auto Combat: {prompt}]", is_complete=True)]
    )


async def send_initial_combat_prompt(event_bus: IEventBus, game_id: str, prompt: str) -> None:
    """Broadcast the initial combat system prompt when combat begins."""
    await event_bus.submit_and_wait(
        [BroadcastNarrativeCommand(game_id=game_id, content=f"[Combat System: {prompt}]", is_complete=True)]
    )
