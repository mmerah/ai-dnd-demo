"""Central event bus for processing commands sequentially."""

import asyncio
import logging
from typing import Any

from app.events.base import BaseCommand
from app.events.handlers.base_handler import BaseHandler
from app.events.handlers.broadcast_handler import BroadcastHandler
from app.events.handlers.character_handler import CharacterHandler
from app.events.handlers.dice_handler import DiceHandler
from app.events.handlers.inventory_handler import InventoryHandler
from app.events.handlers.time_handler import TimeHandler
from app.services.dice_service import DiceService
from app.services.game_service import GameService

logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for processing commands sequentially."""

    def __init__(self, game_service: GameService):
        self.game_service = game_service
        self.dice_service = DiceService()

        # Initialize handlers
        self.handlers: dict[str, BaseHandler] = {
            "character": CharacterHandler(game_service),
            "dice": DiceHandler(game_service, self.dice_service),
            "inventory": InventoryHandler(game_service),
            "time": TimeHandler(game_service),
            "broadcast": BroadcastHandler(game_service),
        }

        # Command queue with priority support
        from datetime import datetime

        self.command_queue: asyncio.PriorityQueue[tuple[int, datetime, BaseCommand]] = asyncio.PriorityQueue()
        self.processing = False
        self.processing_task: asyncio.Task[None] | None = None

    async def submit_command(self, command: BaseCommand) -> None:
        """Submit a command to the queue for processing."""
        # Priority queue item: (priority_value, insertion_order, command)
        # Lower priority value = higher priority
        await self.command_queue.put((command.priority.value, command.timestamp, command))
        logger.debug(f"Command submitted: {type(command).__name__} with priority {command.priority.name}")

        # Start processing if not already running
        if not self.processing:
            self.processing_task = asyncio.create_task(self._process_queue())

    async def execute_command(self, command: BaseCommand) -> dict[str, Any] | None:
        """Execute a command synchronously and return its result data.

        This is used by tools to get immediate results from their commands.
        Returns the data field from the CommandResult.
        """
        logger.info(f"Executing command synchronously: {type(command).__name__}")

        # Get game state
        game_state = self.game_service.get_game(command.game_id)
        if not game_state:
            raise ValueError(f"Game {command.game_id} not found")

        # Find handler
        handler_name = command.get_handler_name()
        handler = self.handlers.get(handler_name)

        if not handler:
            raise ValueError(f"No handler found for {handler_name}")

        if not handler.can_handle(command):
            raise ValueError(f"Handler {handler_name} cannot handle {type(command).__name__}")

        # Execute command
        result = await handler.handle(command, game_state)

        if not result.success:
            logger.error(f"Command failed: {result.error}")
            raise RuntimeError(f"Command execution failed: {result.error}")

        # Process follow-up commands asynchronously (don't wait)
        if result.follow_up_commands:
            logger.debug(f"Submitting {len(result.follow_up_commands)} follow-up commands")
            await self.submit_commands(result.follow_up_commands)

        # Return the result data
        return result.data

    async def submit_commands(self, commands: list[BaseCommand]) -> None:
        """Submit multiple commands to the queue."""
        for command in commands:
            await self.submit_command(command)

    async def _process_queue(self) -> None:
        """Process commands from the queue sequentially."""
        self.processing = True

        try:
            while not self.command_queue.empty():
                # Get next command (priority queue returns tuple)
                _, _, command = await self.command_queue.get()

                try:
                    await self._process_command(command)
                except Exception as e:
                    logger.error(f"Error processing command {type(command).__name__}: {e}", exc_info=True)
                    # Fail fast - re-raise the exception
                    raise
        finally:
            self.processing = False

    async def _process_command(self, command: BaseCommand) -> None:
        """Process a single command."""
        logger.info(f"Processing command: {type(command).__name__}")

        # Get game state
        game_state = self.game_service.get_game(command.game_id)
        if not game_state:
            raise ValueError(f"Game {command.game_id} not found")

        # Find handler
        handler_name = command.get_handler_name()
        handler = self.handlers.get(handler_name)

        if not handler:
            raise ValueError(f"No handler found for {handler_name}")

        if not handler.can_handle(command):
            raise ValueError(f"Handler {handler_name} cannot handle {type(command).__name__}")

        # Execute command
        result = await handler.handle(command, game_state)

        if not result.success:
            logger.error(f"Command failed: {result.error}")
            raise RuntimeError(f"Command execution failed: {result.error}")

        # Process follow-up commands
        if result.follow_up_commands:
            logger.debug(f"Processing {len(result.follow_up_commands)} follow-up commands")
            await self.submit_commands(result.follow_up_commands)

    async def wait_for_completion(self) -> None:
        """Wait for all queued commands to complete."""
        if self.processing_task:
            await self.processing_task


# Singleton instance
_event_bus: EventBus | None = None


def get_event_bus(game_service: GameService) -> EventBus:
    """Get or create the event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(game_service)
    return _event_bus
