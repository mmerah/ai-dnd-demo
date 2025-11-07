/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type ToolName = string;
export type Result =
  | UpdateHPResult
  | AddConditionResult
  | RemoveConditionResult
  | UpdateSpellSlotsResult
  | ModifyCurrencyResult
  | AddItemResult
  | RemoveItemResult
  | ShortRestResult
  | LongRestResult
  | AdvanceTimeResult
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
  | ToolErrorResult
  | AddPartyMemberResult
  | RemovePartyMemberResult;
export type Type = string;
export type Target = string;
export type OldHp = number;
export type NewHp = number;
export type MaxHp = number;
export type Amount = number;
export type DamageType = string;
export type IsHealing = boolean;
export type IsUnconscious = boolean;
export type Type1 = string;
export type Target1 = string;
export type Condition = string;
export type Duration = number;
export type Type2 = string;
export type Target2 = string;
export type Condition1 = string;
export type Removed = boolean;
export type Type3 = string;
export type Target3 = string;
export type Level = number;
export type OldSlots = number;
export type NewSlots = number;
export type MaxSlots = number;
export type Change = number;
export type Type4 = string;
export type OldGold = number;
export type OldSilver = number;
export type OldCopper = number;
export type NewGold = number;
export type NewSilver = number;
export type NewCopper = number;
export type ChangeGold = number;
export type ChangeSilver = number;
export type ChangeCopper = number;
export type Type5 = string;
export type ItemIndex = string;
export type Quantity = number;
export type TotalQuantity = number;
export type Type6 = string;
export type ItemIndex1 = string;
export type Quantity1 = number;
export type RemainingQuantity = number;
export type Type7 = string;
export type OldHp1 = number;
export type NewHp1 = number;
export type Healing = number;
export type Time = string;
export type Type8 = string;
export type OldHp2 = number;
export type NewHp2 = number;
export type ConditionsRemoved = string[];
export type SpellSlotsRestored = boolean;
export type Time1 = string;
export type Type9 = string;
export type OldTime = string;
export type NewTime = string;
export type MinutesAdvanced = number;
export type Type10 = string;
export type LocationId = string;
export type LocationName = string;
export type Description = string | null;
export type Message = string;
export type Type11 = string;
export type SecretId = string;
export type Description1 = string;
export type Message1 = string;
export type Type12 = string;
export type LocationId1 = string;
export type Updates = string[];
export type Message2 = string;
export type Type13 = string;
export type NpcId = string;
export type NpcName = string;
export type FromLocationId = string;
export type ToLocationId = string;
export type Message3 = string;
export type Type14 = string;
export type CombatStarted = boolean;
export type EntityId = string;
/**
 * Allowed runtime entity categories used in combat and lookups.
 */
export type EntityType = 'player' | 'npc' | 'monster';
/**
 * Faction for combat participants.
 */
export type CombatFaction = 'player' | 'ally' | 'enemy' | 'neutral';
export type Name = string;
export type Initiative = number | null;
export type IsPlayer = boolean;
export type IsActive = boolean;
export type Participants = CombatParticipant[];
export type Message4 = string;
export type Type15 = string;
export type EncounterId = string;
export type EncounterType = string;
export type Participants1 = CombatParticipant[];
export type Message5 = string;
export type Type16 = string;
export type MonstersSpawned = CombatParticipant[];
export type Message6 = string;
export type Type17 = string;
export type RoundNumber = number;
export type Message7 = string;
export type Type18 = string;
export type Message8 = string;
export type Type19 = string;
export type Message9 = string;
export type Type20 = string;
export type EntityId1 = string;
export type Message10 = string;
export type Type21 = string;
export type RollType = string;
export type Dice = string;
export type Modifier = number;
export type Rolls = number[];
export type Total = number;
export type Ability = string | null;
export type Skill = string | null;
export type Critical = boolean | null;
export type Type22 = string;
export type Target4 = string;
export type OldLevel = number;
export type NewLevel = number;
export type OldMaxHp = number;
export type NewMaxHp = number;
export type HpIncrease = number;
export type Message11 = string;
export type Type23 = string;
export type ItemIndex2 = string;
export type Equipped = boolean;
export type Slot = string | null;
export type Message12 = string;
export type Type24 = string;
export type Error = string;
export type ToolName1 = string;
export type Suggestion = string | null;
export type Type25 = string;
export type NpcId1 = string;
export type NpcName1 = string;
export type PartySize = number;
export type Message13 = string;
export type Type26 = string;
export type NpcId2 = string;
export type NpcName2 = string;
export type PartySize1 = number;
export type Message14 = string;

/**
 * Data for tool result events.
 */
export interface ToolResultData {
  timestamp?: Timestamp;
  tool_name: ToolName;
  result: Result;
}
export interface UpdateHPResult {
  type?: Type;
  target: Target;
  old_hp: OldHp;
  new_hp: NewHp;
  max_hp: MaxHp;
  amount: Amount;
  damage_type: DamageType;
  is_healing: IsHealing;
  is_unconscious: IsUnconscious;
}
export interface AddConditionResult {
  type?: Type1;
  target: Target1;
  condition: Condition;
  duration: Duration;
}
export interface RemoveConditionResult {
  type?: Type2;
  target: Target2;
  condition: Condition1;
  removed: Removed;
}
export interface UpdateSpellSlotsResult {
  type?: Type3;
  target: Target3;
  level: Level;
  old_slots: OldSlots;
  new_slots: NewSlots;
  max_slots: MaxSlots;
  change: Change;
}
export interface ModifyCurrencyResult {
  type?: Type4;
  old_gold: OldGold;
  old_silver: OldSilver;
  old_copper: OldCopper;
  new_gold: NewGold;
  new_silver: NewSilver;
  new_copper: NewCopper;
  change_gold: ChangeGold;
  change_silver: ChangeSilver;
  change_copper: ChangeCopper;
}
export interface AddItemResult {
  type?: Type5;
  item_index: ItemIndex;
  quantity: Quantity;
  total_quantity: TotalQuantity;
}
export interface RemoveItemResult {
  type?: Type6;
  item_index: ItemIndex1;
  quantity: Quantity1;
  remaining_quantity: RemainingQuantity;
}
export interface ShortRestResult {
  type?: Type7;
  old_hp: OldHp1;
  new_hp: NewHp1;
  healing: Healing;
  time: Time;
}
export interface LongRestResult {
  type?: Type8;
  old_hp: OldHp2;
  new_hp: NewHp2;
  conditions_removed: ConditionsRemoved;
  spell_slots_restored: SpellSlotsRestored;
  time: Time1;
}
export interface AdvanceTimeResult {
  type?: Type9;
  old_time: OldTime;
  new_time: NewTime;
  minutes_advanced: MinutesAdvanced;
}
export interface ChangeLocationResult {
  type?: Type10;
  location_id: LocationId;
  location_name: LocationName;
  description: Description;
  message: Message;
}
export interface DiscoverSecretResult {
  type?: Type11;
  secret_id: SecretId;
  description: Description1;
  message: Message1;
}
export interface UpdateLocationStateResult {
  type?: Type12;
  location_id: LocationId1;
  updates: Updates;
  message: Message2;
}
export interface MoveNPCResult {
  type?: Type13;
  npc_id: NpcId;
  npc_name: NpcName;
  from_location_id: FromLocationId;
  to_location_id: ToLocationId;
  message: Message3;
}
export interface StartCombatResult {
  type?: Type14;
  combat_started: CombatStarted;
  participants: Participants;
  message: Message4;
}
/**
 * Participant in combat with initiative and stable entity reference.
 */
export interface CombatParticipant {
  entity_id: EntityId;
  entity_type: EntityType;
  faction: CombatFaction;
  name: Name;
  initiative?: Initiative;
  is_player?: IsPlayer;
  is_active?: IsActive;
}
export interface StartEncounterCombatResult {
  type?: Type15;
  encounter_id: EncounterId;
  encounter_type: EncounterType;
  participants: Participants1;
  message: Message5;
}
export interface SpawnMonstersResult {
  type?: Type16;
  monsters_spawned: MonstersSpawned;
  message: Message6;
}
export interface NextTurnResult {
  type?: Type17;
  round_number: RoundNumber;
  current_turn: CombatParticipant | null;
  message: Message7;
}
export interface EndCombatResult {
  type?: Type18;
  message: Message8;
}
export interface AddParticipantResult {
  type?: Type19;
  participant: CombatParticipant;
  message: Message9;
}
export interface RemoveParticipantResult {
  type?: Type20;
  entity_id: EntityId1;
  message: Message10;
}
export interface RollDiceResult {
  type: Type21;
  roll_type: RollType;
  dice: Dice;
  modifier: Modifier;
  rolls: Rolls;
  total: Total;
  ability?: Ability;
  skill?: Skill;
  critical?: Critical;
}
export interface LevelUpResult {
  type?: Type22;
  target: Target4;
  old_level: OldLevel;
  new_level: NewLevel;
  old_max_hp: OldMaxHp;
  new_max_hp: NewMaxHp;
  hp_increase: HpIncrease;
  message: Message11;
}
export interface EquipItemResult {
  type?: Type23;
  item_index: ItemIndex2;
  equipped: Equipped;
  slot?: Slot;
  message: Message12;
}
export interface ToolErrorResult {
  type?: Type24;
  error: Error;
  tool_name: ToolName1;
  suggestion?: Suggestion;
}
export interface AddPartyMemberResult {
  type?: Type25;
  npc_id: NpcId1;
  npc_name: NpcName1;
  party_size: PartySize;
  message: Message13;
}
export interface RemovePartyMemberResult {
  type?: Type26;
  npc_id: NpcId2;
  npc_name: NpcName2;
  party_size: PartySize1;
  message: Message14;
}
