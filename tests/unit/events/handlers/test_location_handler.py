"""Unit tests for LocationHandler."""

from unittest.mock import create_autospec

import pytest

from app.events.commands.location_commands import (
    ChangeLocationCommand,
    DiscoverSecretCommand,
    MoveNPCCommand,
    UpdateLocationStateCommand,
)
from app.events.handlers.location_handler import LocationHandler
from app.interfaces.services.game import ILocationService
from app.interfaces.services.memory import IMemoryService
from app.models.memory import MemoryEventKind, WorldEventContext
from app.models.tool_results import (
    ChangeLocationResult,
    DiscoverSecretResult,
    MoveNPCResult,
    UpdateLocationStateResult,
)
from tests.factories import make_game_state, make_location, make_npc_instance, make_npc_sheet


class TestLocationHandler:
    """Test LocationHandler command processing."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.location_service = create_autospec(ILocationService, instance=True)
        self.memory_service = create_autospec(IMemoryService, instance=True)
        self.handler = LocationHandler(self.location_service, self.memory_service)
        self.game_state = make_game_state()

    @pytest.mark.asyncio
    async def test_change_location(self) -> None:
        """Test changing location."""
        new_location = make_location(
            location_id="forest",
            name="Dark Forest",
            description="A mysterious forest.",
        )
        self.game_state.scenario_instance.sheet.progression.acts[0].locations.append(new_location.id)
        self.game_state.scenario_instance.sheet.locations.append(new_location)

        command = ChangeLocationCommand(
            game_id=self.game_state.game_id,
            location_id=new_location.id,
            location_name=new_location.name,
            description="A mysterious forest shrouded in fog.",
        )

        result = await self.handler.handle(command, self.game_state)

        self.location_service.move_entity.assert_called_once_with(
            self.game_state,
            entity_id=None,
            to_location_id=new_location.id,
            location_name=new_location.name,
            description=command.description,
        )
        self.memory_service.on_location_exit.assert_awaited_once_with(self.game_state)

        assert result.mutated
        assert isinstance(result.data, ChangeLocationResult)
        assert result.data.location_id == new_location.id

    @pytest.mark.asyncio
    async def test_discover_secret(self) -> None:
        """Test discovering a secret."""
        secret_desc = "A hidden passage behind the bookshelf!"
        self.location_service.discover_secret.return_value = secret_desc

        command = DiscoverSecretCommand(
            game_id=self.game_state.game_id,
            secret_id="hidden-passage",
            secret_description=secret_desc,
        )

        result = await self.handler.handle(command, self.game_state)

        assert result.mutated
        assert isinstance(result.data, DiscoverSecretResult)
        assert result.data.secret_id == command.secret_id
        assert result.data.description == secret_desc

    @pytest.mark.asyncio
    async def test_move_npc(self) -> None:
        """Test moving an NPC."""
        npc_sheet = make_npc_sheet(
            npc_id="town-guard-npc", display_name="Town Guard", initial_location_id="town-square"
        )
        npc = make_npc_instance(
            npc_sheet=npc_sheet,
            instance_id="npc-guard-1",
            scenario_npc_id="town-guard",
            current_location_id="town-square",
        )
        self.game_state.npcs.append(npc)

        target_location = make_location(
            location_id="tavern",
            name="The Rusty Dragon",
            description="A cozy tavern.",
        )
        self.game_state.scenario_instance.sheet.locations.append(target_location)

        command = MoveNPCCommand(
            game_id=self.game_state.game_id,
            npc_id=npc.instance_id,
            to_location_id=target_location.id,
        )

        prev_location_id = npc.current_location_id

        result = await self.handler.handle(command, self.game_state)

        assert result.mutated
        assert isinstance(result.data, MoveNPCResult)
        assert result.data.npc_id == npc.instance_id
        assert result.data.npc_name == npc.display_name
        assert result.data.from_location_id == prev_location_id
        assert result.data.to_location_id == target_location.id

    @pytest.mark.asyncio
    async def test_update_location_state(self) -> None:
        """Test updating location state."""
        location_id = "forest"
        updates = ["Danger level: CLEARED", "Completed encounter: ambush"]
        self.location_service.update_location_state.return_value = (location_id, updates)

        command = UpdateLocationStateCommand(
            game_id=self.game_state.game_id,
            location_id=location_id,
            danger_level="CLEARED",
            complete_encounter="ambush",
        )

        result = await self.handler.handle(command, self.game_state)

        assert result.mutated
        assert isinstance(result.data, UpdateLocationStateResult)
        assert result.data.location_id == location_id
        assert result.data.updates == updates
        await_calls = self.memory_service.on_world_event.await_args_list
        assert len(await_calls) == 2
        event_kinds = [call.kwargs["event_kind"] for call in await_calls]
        assert MemoryEventKind.LOCATION_CLEARED in event_kinds
        assert MemoryEventKind.ENCOUNTER_COMPLETED in event_kinds
        contexts = [call.kwargs["context"] for call in await_calls]
        assert all(isinstance(ctx, WorldEventContext) for ctx in contexts)

    @pytest.mark.asyncio
    async def test_invalid_npc_error(self) -> None:
        """Test error for invalid NPC."""
        command = MoveNPCCommand(
            game_id=self.game_state.game_id,
            npc_id="non-existent",
            to_location_id="tavern",
        )

        with pytest.raises(ValueError, match="NPC with id"):
            await self.handler.handle(command, self.game_state)

    @pytest.mark.asyncio
    async def test_empty_location_id_error(self) -> None:
        """Test error for empty location ID."""
        command = ChangeLocationCommand(
            game_id=self.game_state.game_id,
            location_id="",
            location_name="Nowhere",
        )

        with pytest.raises(ValueError, match="Location ID cannot be empty"):
            await self.handler.handle(command, self.game_state)
