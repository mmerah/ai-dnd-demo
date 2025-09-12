"""Typed models for tool results to eliminate dict[str, Any] usage."""

from pydantic import BaseModel

from app.models.combat import CombatParticipant


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


class MoveNPCResult(BaseModel):
    type: str = "move_npc"
    npc_id: str
    npc_name: str
    from_location_id: str
    to_location_id: str
    message: str


class StartCombatResult(BaseModel):
    type: str = "start_combat"
    combat_started: bool
    participants: list[CombatParticipant]
    message: str


class StartEncounterCombatResult(BaseModel):
    type: str = "trigger_encounter"
    encounter_id: str
    encounter_type: str
    participants: list[CombatParticipant]
    message: str


class SpawnMonstersResult(BaseModel):
    type: str = "spawn_monsters"
    monsters_spawned: list[CombatParticipant]
    message: str


class NextTurnResult(BaseModel):
    type: str = "next_turn"
    round_number: int
    current_turn: CombatParticipant | None
    message: str


class EndCombatResult(BaseModel):
    type: str = "end_combat"
    message: str


class AddParticipantResult(BaseModel):
    type: str = "add_participant"
    participant: CombatParticipant
    message: str


class RemoveParticipantResult(BaseModel):
    type: str = "remove_participant"
    entity_id: str
    message: str


class RollDiceResult(BaseModel):
    type: str
    roll_type: str
    dice: str
    modifier: int
    rolls: list[int]
    total: int
    ability: str | None = None
    skill: str | None = None
    critical: bool | None = None


class LevelUpResult(BaseModel):
    type: str = "level_up"
    old_level: int
    new_level: int
    old_max_hp: int
    new_max_hp: int
    hp_increase: int
    message: str


class EquipItemResult(BaseModel):
    type: str = "equip_item"
    item_name: str
    equipped: bool
    equipped_quantity: int
    message: str


# Union type representing any possible successful result from a tool
ToolResult = (
    UpdateHPResult
    | AddConditionResult
    | RemoveConditionResult
    | UpdateSpellSlotsResult
    | ModifyCurrencyResult
    | AddItemResult
    | RemoveItemResult
    | ShortRestResult
    | LongRestResult
    | AdvanceTimeResult
    | StartQuestResult
    | CompleteObjectiveResult
    | CompleteQuestResult
    | ProgressActResult
    | ChangeLocationResult
    | DiscoverSecretResult
    | UpdateLocationStateResult
    | MoveNPCResult
    | StartCombatResult
    | StartEncounterCombatResult
    | SpawnMonstersResult
    | NextTurnResult
    | EndCombatResult
    | AddParticipantResult
    | RemoveParticipantResult
    | RollDiceResult
    | LevelUpResult
    | EquipItemResult
)
