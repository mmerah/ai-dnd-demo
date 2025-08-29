"""Command definitions for event-driven architecture."""

from app.events.commands.broadcast_commands import (
    BroadcastCharacterUpdateCommand,
    BroadcastGameUpdateCommand,
    BroadcastNarrativeCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.events.commands.character_commands import (
    AddConditionCommand,
    RemoveConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.commands.dice_commands import RollDiceCommand
from app.events.commands.inventory_commands import (
    AddItemCommand,
    ModifyCurrencyCommand,
    RemoveItemCommand,
)
from app.events.commands.time_commands import (
    AdvanceTimeCommand,
    LongRestCommand,
    ShortRestCommand,
)

__all__ = [
    # Character commands
    "UpdateHPCommand",
    "AddConditionCommand",
    "RemoveConditionCommand",
    "UpdateSpellSlotsCommand",
    # Dice commands
    "RollDiceCommand",
    # Inventory commands
    "ModifyCurrencyCommand",
    "AddItemCommand",
    "RemoveItemCommand",
    # Time commands
    "ShortRestCommand",
    "LongRestCommand",
    "AdvanceTimeCommand",
    # Broadcast commands
    "BroadcastNarrativeCommand",
    "BroadcastToolCallCommand",
    "BroadcastToolResultCommand",
    "BroadcastGameUpdateCommand",
    "BroadcastCharacterUpdateCommand",
]
