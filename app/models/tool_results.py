"""Typed models for tool results to eliminate dict[str, Any] usage."""

from pydantic import BaseModel


class UpdateHPResult(BaseModel):
    type: str = "hp_update"
    target: str
    old_hp: int
    new_hp: int
    max_hp: int
    amount: int
    damage_type: str
    is_healing: bool
    is_unconscious: bool


class AddConditionResult(BaseModel):
    type: str = "add_condition"
    target: str
    condition: str
    duration: int


class RemoveConditionResult(BaseModel):
    type: str = "remove_condition"
    target: str
    condition: str
    removed: bool


class UpdateSpellSlotsResult(BaseModel):
    type: str = "spell_slots_update"
    level: int
    old_slots: int
    new_slots: int
    max_slots: int
    change: int


class ModifyCurrencyResult(BaseModel):
    type: str = "currency_update"
    old_gold: int
    old_silver: int
    old_copper: int
    new_gold: int
    new_silver: int
    new_copper: int
    change_gold: int
    change_silver: int
    change_copper: int


class AddItemResult(BaseModel):
    type: str = "item_added"
    item_name: str
    quantity: int
    total_quantity: int


class RemoveItemResult(BaseModel):
    type: str = "item_removed"
    item_name: str
    quantity: int
    remaining_quantity: int


class ShortRestResult(BaseModel):
    type: str = "short_rest"
    old_hp: int
    new_hp: int
    healing: int
    time: str


class LongRestResult(BaseModel):
    type: str = "long_rest"
    old_hp: int
    new_hp: int
    conditions_removed: list[str]
    spell_slots_restored: bool
    time: str


class AdvanceTimeResult(BaseModel):
    type: str = "time_advance"
    old_time: str
    new_time: str
    minutes_advanced: int


class RollDiceResult(BaseModel):
    type: str
    roll_type: str
    dice: str
    modifier: int
    rolls: list[int]
    total: int
    target: str | None = None
    ability: str | None = None
    skill: str | None = None
    damage_type: str | None = None
    dc: int | None = None
    critical: bool | None = None
    source: str | None = None
    weapon_name: str | None = None
    attacker: str | None = None
    combatants: list[str] | None = None
