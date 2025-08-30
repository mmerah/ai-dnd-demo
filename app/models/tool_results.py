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


class QuestAvailabilityResult(BaseModel):
    type: str = "quest_availability"
    available: bool
    message: str
    missing_prerequisites: list[str] | None = None


class ObjectiveStatusResult(BaseModel):
    type: str = "objective_status"
    quest_id: str
    objective_id: str
    status: str
    message: str


class StartQuestResult(BaseModel):
    type: str = "start_quest"
    quest_id: str
    quest_name: str
    objectives: list[dict[str, str]]
    message: str


class CompleteObjectiveResult(BaseModel):
    type: str = "complete_objective"
    quest_id: str
    objective_id: str
    quest_complete: bool
    progress: float
    message: str


class CompleteQuestResult(BaseModel):
    type: str = "complete_quest"
    quest_id: str
    quest_name: str
    rewards: str | None
    message: str


class ProgressActResult(BaseModel):
    type: str = "progress_act"
    new_act_id: str
    new_act_name: str
    message: str


class SearchLocationResult(BaseModel):
    type: str = "search_location"
    success: bool
    message: str
    discovered: list[str] | None = None


class ChangeLocationResult(BaseModel):
    type: str = "change_location"
    location_id: str
    location_name: str
    description: str | None
    message: str


class DiscoverSecretResult(BaseModel):
    type: str = "discover_secret"
    secret_id: str
    description: str
    message: str


class UpdateLocationStateResult(BaseModel):
    type: str = "update_location_state"
    location_id: str
    updates: list[str]
    message: str


class GroupInitiativeResult(BaseModel):
    type: str = "group_initiative"
    group: str
    roll: int
    modifier: int
    total: int
    message: str


class StartCombatResult(BaseModel):
    type: str = "start_combat"
    combat_started: bool
    participants: list[dict[str, str | int | bool]]
    message: str


class TriggerEncounterResult(BaseModel):
    type: str = "trigger_encounter"
    encounter_id: str
    encounter_type: str
    monsters_spawned: list[dict[str, str | int]]
    message: str


class SpawnMonstersResult(BaseModel):
    type: str = "spawn_monsters"
    monsters_spawned: list[dict[str, str | int]]
    message: str


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
