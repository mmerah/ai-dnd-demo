"""Central event bus for processing commands sequentially using a handler registration pattern."""

import asyncio
import importlib
import inspect
import logging
from datetime import datetime

from pydantic import BaseModel

from app.events.base import BaseCommand, CommandResult
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.events import IEventBus
from app.interfaces.services.character import IEntityStateService
from app.interfaces.services.game import IGameService

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """Central event bus for processing commands sequentially using a handler registration pattern."""

    def __init__(self, game_service: IGameService, entity_state_service: IEntityStateService):
        self.game_service = game_service
        self.entity_state_service = entity_state_service
        self._handlers: dict[str, BaseHandler] = {}

        self.command_queue: asyncio.PriorityQueue[tuple[int, datetime, BaseCommand]] = asyncio.PriorityQueue()
        self.processing = False
        self.processing_task: asyncio.Task[None] | None = None

    def register_handler(self, handler_name: str, handler: BaseHandler) -> None:
        """Register a handler for a specific command domain."""
        self._handlers[handler_name] = handler

    async def submit_command(self, command: BaseCommand) -> None:
        # Priority queue item: (priority_value, insertion_order, command)
        # Lower priority value = higher priority
        await self.command_queue.put((command.priority.value, command.timestamp, command))
        logger.debug(f"Command submitted: {type(command).__name__} with priority {command.priority.name}")
        if not self.processing:
            self.processing_task = asyncio.create_task(self._process_queue())

    async def execute_command(self, command: BaseCommand) -> BaseModel | None:
        result = await self._run_command(command)
        return result.data

    async def submit_commands(self, commands: list[BaseCommand]) -> None:
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
        """Process a single command from the queue."""
        await self._run_command(command)

    async def _run_command(self, command: BaseCommand) -> CommandResult:
        """Core command execution used by both queued and direct execution."""
        logger.info(f"Executing command: {type(command).__name__}")

        # Get game state
        game_state = self.game_service.get_game(command.game_id)

        # Find handler
        handler_name = command.get_handler_name()
        handler = self._handlers.get(handler_name)

        if not handler:
            raise ValueError(f"No handler found for {handler_name}")

        if not handler.can_handle(command):
            raise ValueError(f"Handler {handler_name} cannot handle {type(command).__name__}")

        # Execute command with handlers raising exceptions for errors
        result = await handler.handle(command, game_state)

        # Recompute entity state if needed (player + all party NPCs)
        if result.mutated or result.recompute_state:
            self.entity_state_service.recompute_entity_state(game_state, game_state.character.instance_id)
            if game_state.party.member_ids:
                for npc_id in game_state.party.member_ids:
                    self.entity_state_service.recompute_entity_state(game_state, npc_id)

        # Centralized persistence: save once if handler mutated state
        if result.mutated:
            self.game_service.save_game(game_state)

        # Process follow-up commands
        if result.follow_up_commands:
            logger.debug(f"Processing {len(result.follow_up_commands)} follow-up commands")
            await self.submit_commands(result.follow_up_commands)

        return result

    async def wait_for_completion(self) -> None:
        if self.processing_task:
            await self.processing_task

    async def submit_and_wait(self, commands: list[BaseCommand]) -> None:
        await self.submit_commands(commands)
        await self.wait_for_completion()

    # Verification utilities
    def verify_handlers(self) -> None:
        """Verify that all commands have a registered handler that can handle them."""
        # List of command modules to introspect
        modules = [
            "app.events.commands.entity_commands",
            "app.events.commands.dice_commands",
            "app.events.commands.inventory_commands",
            "app.events.commands.time_commands",
            "app.events.commands.location_commands",
            "app.events.commands.combat_commands",
            "app.events.commands.party_commands",
            "app.events.commands.broadcast_commands",
        ]

        errors: list[str] = []

        for mod_name in modules:
            try:
                mod = importlib.import_module(mod_name)
            except Exception as e:
                errors.append(f"Failed to import {mod_name}: {e}")
                continue

            for _name, obj in inspect.getmembers(mod, inspect.isclass):
                if not issubclass(obj, BaseCommand) or obj is BaseCommand:
                    continue
                # Instantiate with defaults; BaseCommand provides game_id default
                try:
                    cmd = obj()
                except Exception as e:
                    errors.append(f"Cannot instantiate command {obj.__name__}: {e}")
                    continue

                handler_name = cmd.get_handler_name()
                handler = self._handlers.get(handler_name)
                if not handler:
                    errors.append(
                        f"No handler registered for domain '{handler_name}' to handle {obj.__name__}",
                    )
                    continue
                try:
                    # Prefer declarative supported_commands if present
                    supported = getattr(handler, "supported_commands", None)
                    if supported is not None:
                        if not isinstance(cmd, supported):
                            errors.append(
                                f"Handler '{handler_name}' supported_commands missing {obj.__name__}",
                            )
                    else:
                        if not handler.can_handle(cmd):
                            errors.append(
                                f"Handler '{handler_name}' cannot handle command {obj.__name__}",
                            )
                except Exception as e:
                    errors.append(
                        f"Error checking handler '{handler_name}' for {obj.__name__}: {e}",
                    )

        if errors:
            raise ValueError(
                "Handler verification failed:\n" + "\n".join(f"- {msg}" for msg in errors),
            )
