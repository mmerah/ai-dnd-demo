"""Central event bus for processing commands sequentially using a handler registration pattern."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from app.events.base import BaseCommand
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.events import IEventBus
from app.interfaces.services import IGameService

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """Central event bus for processing commands sequentially using a handler registration pattern."""

    def __init__(self, game_service: IGameService):
        self.game_service = game_service
        self._handlers: dict[str, BaseHandler] = {}

        self.command_queue: asyncio.PriorityQueue[tuple[int, datetime, BaseCommand]] = asyncio.PriorityQueue()
        self.processing = False
        self.processing_task: asyncio.Task[None] | None = None

    def register_handler(self, handler_name: str, handler: BaseHandler) -> None:
        """Register a handler for a specific command domain."""
        self._handlers[handler_name] = handler

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
        handler = self._handlers.get(handler_name)

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
        handler = self._handlers.get(handler_name)

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
