"""Command definitions for event-driven architecture."""

from app.events.commands.broadcast_commands import (
    BroadcastGameUpdateCommand,
    BroadcastNarrativeCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.events.commands.character_commands import (
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.commands.dice_commands import RollDiceCommand
from app.events.commands.inventory_commands import (
    ModifyCurrencyCommand,
    ModifyInventoryCommand,
)
from app.events.commands.time_commands import (
    AdvanceTimeCommand,
    LongRestCommand,
    ShortRestCommand,
)

__all__ = [
    # Character commands
    "UpdateHPCommand",
    "UpdateConditionCommand",
    "UpdateSpellSlotsCommand",
    # Dice commands
    "RollDiceCommand",
    # Inventory commands
    "ModifyCurrencyCommand",
    "ModifyInventoryCommand",
    # Time commands
    "ShortRestCommand",
    "LongRestCommand",
    "AdvanceTimeCommand",
    # Broadcast commands
    "BroadcastNarrativeCommand",
    "BroadcastToolCallCommand",
    "BroadcastToolResultCommand",
    "BroadcastGameUpdateCommand",
]
