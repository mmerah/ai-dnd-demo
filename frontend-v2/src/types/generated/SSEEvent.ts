/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * All possible SSE event types.
 */
export type SSEEventType =
  | 'connected'
  | 'heartbeat'
  | 'narrative'
  | 'initial_narrative'
  | 'tool_call'
  | 'tool_result'
  | 'dice_roll'
  | 'combat_update'
  | 'combat_suggestion'
  | 'system'
  | 'npc_dialogue'
  | 'policy_warning'
  | 'error'
  | 'game_update'
  | 'scenario_info'
  | 'complete';
export type Data =
  | ConnectedData
  | HeartbeatData
  | NarrativeData
  | InitialNarrativeData
  | ToolCallData
  | ToolResultData
  | NPCDialogueData
  | CombatUpdateData
  | CombatSuggestionData
  | SystemMessageData
  | PolicyWarningData
  | ErrorData
  | GameUpdateData
  | ScenarioInfoData
  | CompleteData;
export type Timestamp = string;
export type GameId = string;
export type Status = 'connected';
export type Timestamp1 = string;
export type Timestamp2 = string;
export type Word = string | null;
export type Complete = boolean | null;
export type Start = boolean | null;
export type Content = string | null;
export type Timestamp3 = string;
export type ScenarioTitle = string;
export type Narrative = string;
export type Timestamp4 = string;
export type ToolName = string;
export type Timestamp5 = string;
export type ToolName1 = string;
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
export type ToolName2 = string;
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
export type Timestamp6 = string;
export type NpcId3 = string;
export type NpcName3 = string;
export type Content1 = string;
export type Complete1 = boolean;
export type Timestamp7 = string;
export type RoundNumber1 = number;
export type TurnIndex = number;
export type Participants2 = CombatParticipant[];
export type IsActive1 = boolean;
/**
 * Combat phase for explicit state tracking.
 */
export type CombatPhase = 'inactive' | 'starting' | 'active' | 'auto_ending' | 'ended';
export type CombatOccurrence = number;
export type Timestamp8 = string;
/**
 * Unique identifier for this suggestion
 */
export type SuggestionId = string;
/**
 * Instance ID of the NPC making the suggestion
 */
export type NpcId4 = string;
/**
 * Display name of the NPC
 */
export type NpcName4 = string;
/**
 * Simple description of the suggested action from NPC perspective
 */
export type ActionText = string;
export type Timestamp9 = string;
export type Message15 = string;
export type Level1 = 'info' | 'warning' | 'error';
export type Timestamp10 = string;
export type Message16 = string;
export type ToolName3 = string | null;
export type AgentType = string | null;
export type Timestamp11 = string;
export type Error1 = string;
export type Type27 = string | null;
export type Timestamp12 = string;
export type GameId1 = string;
export type CreatedAt = string;
export type LastSaved = string;
export type InstanceId = string;
export type CreatedAt1 = string;
export type UpdatedAt = string;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type Level2 = number;
export type ExperiencePoints = number;
export type Current = number;
export type Maximum = number;
export type Temporary = number;
export type Total1 = number;
export type Current1 = number;
export type Type28 = string;
export type ArmorClass = number;
export type InitiativeBonus = number;
export type Speed = number;
export type Str1 = number;
export type Dex1 = number;
export type Con1 = number;
export type Int1 = number;
export type Wis1 = number;
export type Cha1 = number;
export type Index = string;
export type Value = number;
export type Skills = SkillValue[];
export type Name1 = string;
export type AttackRollBonus = number;
export type Damage = string;
export type DamageType1 = string;
export type Range = string;
export type Properties = string[];
export type Type29 = string;
export type Reach = string;
export type Special = string;
export type Attacks = AttackAction[];
export type Conditions = string[];
export type ExhaustionLevel = number;
export type Inspiration = boolean;
export type Index1 = string;
export type Name2 = string | null;
/**
 * Types of items in the game.
 */
export type ItemType = 'Weapon' | 'Armor' | 'Potion' | 'Ammunition' | 'Adventuring Gear' | 'Equipment Pack';
export type Quantity2 = number;
export type Inventory = InventoryItem[];
export type Head = string | null;
export type Neck = string | null;
export type Chest = string | null;
export type Hands = string | null;
export type Feet = string | null;
export type Waist = string | null;
export type MainHand = string | null;
export type OffHand = string | null;
export type Ring1 = string | null;
export type Ring2 = string | null;
export type Back = string | null;
export type Ammunition = string | null;
export type Copper = number;
export type Silver = number;
export type Electrum = number;
export type Gold = number;
export type Platinum = number;
/**
 * Spellcasting ability scores.
 */
export type SpellcastingAbility = 'Intelligence' | 'Wisdom' | 'Charisma' | 'INT' | 'WIS' | 'CHA';
export type SpellSaveDc = number | null;
export type SpellAttackBonus = number | null;
export type SpellsKnown = string[];
export type Level3 = number;
export type Total2 = number;
export type Current2 = number;
export type SpellsPrepared = string[];
export type RitualSpells = string[];
export type TemplateId = string;
export type Id = string;
export type Name3 = string;
export type Race = string;
export type ClassIndex = string;
export type Subclass = string | null;
export type Subrace = string | null;
export type ContentPacks = string[];
export type StartingLevel = number;
export type Background = string;
export type Alignment = string;
export type StartingExperiencePoints = number;
export type Name4 = string;
export type Description2 = string;
export type CustomFeatures = CustomFeature[];
export type FeatureIndexes = string[];
export type TraitIndexes = string[];
export type FeatIndexes = string[];
export type StartingSkillIndexes = string[];
export type StartingInventory = InventoryItem[];
export type Traits = string[];
export type Ideals = string[];
export type Bonds = string[];
export type Flaws = string[];
export type Backstory = string;
export type Languages = string[];
export type InstanceId1 = string;
export type CreatedAt2 = string;
export type UpdatedAt1 = string;
export type ScenarioNpcId = string;
export type Id1 = string;
export type DisplayName = string;
export type Role = string;
export type Description3 = string;
export type InitialLocationId = string;
/**
 * Classification for NPC routing importance.
 */
export type NPCImportance = 'major' | 'minor';
export type InitialDialogueHints = string[];
export type InitialAttitude = string | null;
export type InitialNotes = string[];
export type CurrentLocationId = string;
export type Attitude = string | null;
export type CreatedAt3 = string;
/**
 * Scope of a recorded memory.
 */
export type MemorySource = 'location' | 'npc' | 'world';
export type Summary = string;
export type Tags = string[];
export type LocationId2 = string | null;
export type NpcIds = string[];
export type EncounterId1 = string | null;
export type SinceTimestamp = string | null;
export type SinceMessageIndex = number | null;
export type NpcMemories = MemoryEntry[];
export type Npcs = NPCInstance[];
export type InstanceId2 = string;
export type CreatedAt4 = string;
export type UpdatedAt2 = string;
export type TemplateId1 = string;
export type Index2 = string;
export type Name5 = string;
export type Type30 = string;
export type Size = string;
export type Alignment1 = string;
export type ArmorClass1 = number;
export type HitDice1 = string;
export type Speed1 = string;
export type ChallengeRating = number;
export type Skills1 = SkillValue[];
export type Senses = string;
export type Languages1 = string[];
export type Attacks1 = AttackAction[];
export type Name6 = string;
export type Description4 = string;
export type SpecialAbilities = MonsterSpecialAbility[];
export type DamageVulnerabilities = string[];
export type DamageResistances = string[];
export type DamageImmunities = string[];
export type ConditionImmunities = string[];
export type ContentPack = string;
export type CurrentLocationId1 = string;
export type Monsters = MonsterInstance[];
export type ScenarioId = string;
export type ScenarioTitle1 = string;
export type InstanceId3 = string;
export type TemplateId2 = string;
export type CreatedAt5 = string;
export type UpdatedAt3 = string;
export type Id2 = string;
export type Title = string;
export type Description5 = string;
export type StartingLocationId = string;
export type Id3 = string;
export type Name7 = string;
export type Description6 = string;
export type FirstVisit = string;
export type ReturnVisit = string | null;
export type Cleared = string | null;
export type Id4 = string;
export type DisplayName1 = string;
export type Description7 = string | null;
export type NotableMonsters = ScenarioMonster[];
export type EncounterIds = string[];
export type MonsterIds = string[];
export type ToLocationId1 = string;
export type Description8 = string;
export type Direction = string | null;
export type Type31 = string;
export type Description9 = string;
export type RequirementId = string | null;
export type Dc = number | null;
export type IsMet = boolean;
export type Requirements = ConnectionRequirement[];
export type IsVisible = boolean;
export type IsAccessible = boolean;
export type Connections = LocationConnection[];
export type Events = string[];
export type EnvironmentalFeatures = string[];
export type Id5 = string;
export type Description10 = string;
export type DiscoveryMethod = string;
export type Dc1 = number | null;
export type Reward = string | null;
export type Secrets = Secret[];
export type ItemIndex3 = string;
export type QuantityMin = number;
export type QuantityMax = number;
export type Probability = number;
export type Found = boolean;
export type Hidden = boolean;
export type DcToFind = number | null;
export type LootTable = LootEntry[];
export type VictoryConditions = string[];
/**
 * Danger level of a location.
 */
export type DangerLevel = 'safe' | 'low' | 'moderate' | 'high' | 'extreme' | 'cleared';
export type Locations = ScenarioLocation[];
export type Id6 = string;
export type Type32 = string;
export type Description11 = string;
export type Difficulty = string;
/**
 * Type of entity to spawn. Repository is data/monsters, scenario data/scenarios/{id}/monsters.
 */
export type SpawnType = 'repository' | 'scenario';
export type EntityId2 = string;
export type QuantityMin1 = number;
export type QuantityMax1 = number;
export type Probability1 = number;
export type ParticipantSpawns = EncounterParticipantSpawn[];
export type Dc2 = number | null;
export type Rewards = string[];
export type RandomEncounters = Encounter[];
export type ContentPacks1 = string[];
export type CurrentLocationId2 = string;
export type LocationId3 = string;
export type Visited = boolean;
export type TimesVisited = number;
/**
 * Danger level of a location.
 */
export type DangerLevel1 = 'safe' | 'low' | 'moderate' | 'high' | 'extreme' | 'cleared';
export type CompletedEncounters = string[];
export type DiscoveredSecrets = string[];
export type LootedItems = string[];
export type ActiveEffects = string[];
export type LocationMemories = MemoryEntry[];
export type WorldMemories = MemoryEntry[];
export type LastWorldMessageIndex = number;
export type Tags1 = string[];
export type ContentPacks2 = string[];
export type Location = string;
export type Description12 = string;
export type Day = number;
export type Hour = number;
export type Minute = number;
export type MemberIds = string[];
export type MaxSize = number;
export type StoryNotes = string[];
/**
 * Unique identifier for the journal entry
 */
export type EntryId = string;
/**
 * Entry creation timestamp
 */
export type CreatedAt6 = string;
/**
 * Last modification timestamp
 */
export type UpdatedAt4 = string;
/**
 * Journal entry text content
 */
export type Content2 = string;
/**
 * User-defined and auto-linked tags
 *
 * @maxItems 50
 */
export type Tags2 = string[];
/**
 * Auto-linked location ID at time of creation
 */
export type LocationId4 = string | null;
/**
 * Auto-linked NPC IDs if dialogue active
 */
export type NpcIds1 = string[];
/**
 * Whether this entry is pinned to the top of the list
 */
export type Pinned = boolean;
export type PlayerJournalEntries = PlayerJournalEntry[];
/**
 * Message sender role.
 */
export type MessageRole = 'player' | 'dm' | 'npc';
export type Content3 = string;
export type Timestamp13 = string;
/**
 * Types of specialized agents.
 */
export type AgentType1 = 'narrative' | 'combat' | 'summarizer' | 'npc' | 'player' | 'tool_suggestor';
export type Location1 = string | null;
export type NpcsMentioned = string[];
export type CombatRound = number | null;
export type CombatOccurrence1 = number | null;
export type SpeakerNpcId = string | null;
export type SpeakerNpcName = string | null;
export type ConversationHistory = Message17[];
/**
 * Types of game events.
 */
export type GameEventType = 'tool_call' | 'tool_result';
export type Timestamp14 = string;
export type ToolName4 = string;
export type GameEvents = GameEvent[];
export type Active = boolean;
export type TargetNpcIds = string[];
export type StartedAt = string | null;
export type LastInteractionAt = string | null;
/**
 * Supported dialogue session modes.
 */
export type DialogueSessionMode = 'explicit_only' | 'sticky';
/**
 * Types of specialized agents.
 */
export type AgentType2 = 'narrative' | 'combat' | 'summarizer' | 'npc' | 'player' | 'tool_suggestor';
export type SessionNumber = number;
export type TotalPlayTimeMinutes = number;
export type Timestamp15 = string;
export type AvailableScenarios = ScenarioSheet[];
export type Timestamp16 = string;
export type Status1 = 'success' | 'error';

/**
 * Fully typed SSE event.
 */
export interface SSEEvent {
  event: SSEEventType;
  data: Data;
}
/**
 * Data for connected event.
 */
export interface ConnectedData {
  timestamp?: Timestamp;
  game_id: GameId;
  status: Status;
}
/**
 * Data for heartbeat event.
 */
export interface HeartbeatData {
  timestamp?: Timestamp1;
}
/**
 * Data for narrative streaming events.
 */
export interface NarrativeData {
  timestamp?: Timestamp2;
  word?: Word;
  complete?: Complete;
  start?: Start;
  content?: Content;
}
/**
 * Data for initial narrative event.
 */
export interface InitialNarrativeData {
  timestamp?: Timestamp3;
  scenario_title: ScenarioTitle;
  narrative: Narrative;
}
/**
 * Data for tool call events.
 */
export interface ToolCallData {
  timestamp?: Timestamp4;
  tool_name: ToolName;
  parameters: Parameters;
}
export interface Parameters {
  [k: string]:
    | string
    | number
    | boolean
    | {
        [k: string]: any;
      }
    | any[]
    | null;
}
/**
 * Data for tool result events.
 */
export interface ToolResultData {
  timestamp?: Timestamp5;
  tool_name: ToolName1;
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
  tool_name: ToolName2;
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
/**
 * Data for NPC dialogue events.
 */
export interface NPCDialogueData {
  timestamp?: Timestamp6;
  npc_id: NpcId3;
  npc_name: NpcName3;
  content: Content1;
  complete?: Complete1;
}
/**
 * Data for combat update events.
 */
export interface CombatUpdateData {
  timestamp?: Timestamp7;
  combat: CombatState;
}
/**
 * Combat encounter state.
 */
export interface CombatState {
  round_number?: RoundNumber1;
  turn_index?: TurnIndex;
  participants?: Participants2;
  is_active?: IsActive1;
  phase?: CombatPhase;
  combat_occurrence?: CombatOccurrence;
}
/**
 * Data for combat suggestion events from allied NPCs.
 */
export interface CombatSuggestionData {
  timestamp?: Timestamp8;
  suggestion: CombatSuggestion;
}
/**
 * Combat action suggestion from an allied NPC.
 *
 * Used when an allied NPC's turn comes up in combat to suggest an action
 * to the player for approval before execution.
 */
export interface CombatSuggestion {
  suggestion_id: SuggestionId;
  npc_id: NpcId4;
  npc_name: NpcName4;
  action_text: ActionText;
}
/**
 * Data for system message events.
 */
export interface SystemMessageData {
  timestamp?: Timestamp9;
  message: Message15;
  level?: Level1;
}
/**
 * Data for explicit policy warning events (tool gating, etc.).
 */
export interface PolicyWarningData {
  timestamp?: Timestamp10;
  message: Message16;
  tool_name?: ToolName3;
  agent_type?: AgentType;
}
/**
 * Data for error events.
 */
export interface ErrorData {
  timestamp?: Timestamp11;
  error: Error1;
  type?: Type27;
}
/**
 * Data for complete game state update events.
 */
export interface GameUpdateData {
  timestamp?: Timestamp12;
  game_state: GameState;
}
/**
 * Complete game state for a D&D session.
 */
export interface GameState {
  game_id: GameId1;
  created_at?: CreatedAt;
  last_saved?: LastSaved;
  character: CharacterInstance;
  npcs?: Npcs;
  monsters?: Monsters;
  scenario_id: ScenarioId;
  scenario_title: ScenarioTitle1;
  scenario_instance: ScenarioInstance;
  content_packs?: ContentPacks2;
  location?: Location;
  description?: Description12;
  game_time?: GameTime;
  combat?: CombatState;
  party?: PartyState;
  story_notes?: StoryNotes;
  player_journal_entries?: PlayerJournalEntries;
  conversation_history?: ConversationHistory;
  game_events?: GameEvents;
  dialogue_session?: DialogueSessionState;
  active_agent?: AgentType2;
  session_number?: SessionNumber;
  total_play_time_minutes?: TotalPlayTimeMinutes;
}
/**
 * Dynamic character state.
 */
export interface CharacterInstance {
  instance_id: InstanceId;
  created_at?: CreatedAt1;
  updated_at?: UpdatedAt;
  state: EntityState;
  template_id: TemplateId;
  sheet: CharacterSheet;
}
export interface EntityState {
  abilities: Abilities;
  level?: Level2;
  experience_points?: ExperiencePoints;
  hit_points: HitPoints;
  hit_dice: HitDice;
  armor_class?: ArmorClass;
  initiative_bonus?: InitiativeBonus;
  speed?: Speed;
  saving_throws?: SavingThrows;
  skills?: Skills;
  attacks?: Attacks;
  conditions?: Conditions;
  exhaustion_level?: ExhaustionLevel;
  inspiration?: Inspiration;
  inventory?: Inventory;
  equipment_slots?: EquipmentSlots;
  currency: Currency;
  spellcasting?: Spellcasting | null;
}
/**
 * Character ability scores.
 */
export interface Abilities {
  STR: Str;
  DEX: Dex;
  CON: Con;
  INT: Int;
  WIS: Wis;
  CHA: Cha;
}
export interface HitPoints {
  current: Current;
  maximum: Maximum;
  temporary?: Temporary;
}
export interface HitDice {
  total: Total1;
  current: Current1;
  type: Type28;
}
/**
 * Saving throw modifiers by ability.
 */
export interface SavingThrows {
  STR?: Str1;
  DEX?: Dex1;
  CON?: Con1;
  INT?: Int1;
  WIS?: Wis1;
  CHA?: Cha1;
}
/**
 * Runtime skill value bound to a skill index.
 */
export interface SkillValue {
  index: Index;
  value: Value;
}
export interface AttackAction {
  name: Name1;
  attack_roll_bonus: AttackRollBonus;
  damage: Damage;
  damage_type: DamageType1;
  range?: Range;
  properties?: Properties;
  type?: Type29;
  reach?: Reach;
  special?: Special;
}
/**
 * Item instance in inventory.
 */
export interface InventoryItem {
  index: Index1;
  name?: Name2;
  item_type?: ItemType | null;
  quantity?: Quantity2;
}
/**
 * Character equipment slots following D&D 5e conventions.
 */
export interface EquipmentSlots {
  head?: Head;
  neck?: Neck;
  chest?: Chest;
  hands?: Hands;
  feet?: Feet;
  waist?: Waist;
  main_hand?: MainHand;
  off_hand?: OffHand;
  ring_1?: Ring1;
  ring_2?: Ring2;
  back?: Back;
  ammunition?: Ammunition;
}
/**
 * Character wealth tracking.
 */
export interface Currency {
  copper?: Copper;
  silver?: Silver;
  electrum?: Electrum;
  gold?: Gold;
  platinum?: Platinum;
}
/**
 * Character spellcasting information.
 */
export interface Spellcasting {
  ability: SpellcastingAbility;
  spell_save_dc?: SpellSaveDc;
  spell_attack_bonus?: SpellAttackBonus;
  spells_known: SpellsKnown;
  spell_slots: SpellSlots;
  spells_prepared?: SpellsPrepared;
  ritual_spells?: RitualSpells;
}
export interface SpellSlots {
  [k: string]: SpellSlot;
}
/**
 * Spell slot tracking for a spell level.
 */
export interface SpellSlot {
  level: Level3;
  total: Total2;
  current: Current2;
}
/**
 * Character template for pre-game selection.
 *
 * Contains base identity and choices only. All dynamic/derived fields
 * live on CharacterInstance at runtime.
 */
export interface CharacterSheet {
  id: Id;
  name: Name3;
  race: Race;
  class_index: ClassIndex;
  subclass?: Subclass;
  subrace?: Subrace;
  content_packs?: ContentPacks;
  starting_level?: StartingLevel;
  background: Background;
  alignment: Alignment;
  starting_experience_points?: StartingExperiencePoints;
  starting_abilities: Abilities;
  custom_features?: CustomFeatures;
  feature_indexes?: FeatureIndexes;
  trait_indexes?: TraitIndexes;
  feat_indexes?: FeatIndexes;
  starting_skill_indexes?: StartingSkillIndexes;
  starting_spellcasting?: Spellcasting | null;
  starting_inventory?: StartingInventory;
  starting_currency: Currency;
  personality: Personality;
  backstory: Backstory;
  languages: Languages;
}
/**
 * Character feature or trait.
 */
export interface CustomFeature {
  name: Name4;
  description: Description2;
}
/**
 * Character personality traits for roleplay.
 */
export interface Personality {
  traits?: Traits;
  ideals?: Ideals;
  bonds?: Bonds;
  flaws?: Flaws;
}
/**
 * Dynamic NPC state.
 */
export interface NPCInstance {
  instance_id: InstanceId1;
  created_at?: CreatedAt2;
  updated_at?: UpdatedAt1;
  state: EntityState;
  scenario_npc_id: ScenarioNpcId;
  sheet: NPCSheet;
  current_location_id: CurrentLocationId;
  attitude?: Attitude;
  npc_memories?: NpcMemories;
}
/**
 * NPC wrapper embedding a full CharacterSheet plus scenario metadata (template-only).
 */
export interface NPCSheet {
  id: Id1;
  display_name: DisplayName;
  role: Role;
  description: Description3;
  initial_location_id: InitialLocationId;
  importance?: NPCImportance;
  initial_dialogue_hints?: InitialDialogueHints;
  initial_attitude?: InitialAttitude;
  initial_notes?: InitialNotes;
  character: CharacterSheet;
}
/**
 * Append-only memory snapshot summarizing recent events.
 */
export interface MemoryEntry {
  created_at?: CreatedAt3;
  source: MemorySource;
  summary: Summary;
  tags?: Tags;
  location_id?: LocationId2;
  npc_ids?: NpcIds;
  encounter_id?: EncounterId1;
  since_timestamp?: SinceTimestamp;
  since_message_index?: SinceMessageIndex;
}
/**
 * Dynamic monster state bound to a MonsterSheet template.
 */
export interface MonsterInstance {
  instance_id: InstanceId2;
  created_at?: CreatedAt4;
  updated_at?: UpdatedAt2;
  state: EntityState;
  template_id: TemplateId1;
  sheet: MonsterSheet;
  current_location_id: CurrentLocationId1;
}
/**
 * Minimal monster stat block (template).
 */
export interface MonsterSheet {
  index: Index2;
  name: Name5;
  type: Type30;
  size: Size;
  alignment: Alignment1;
  armor_class: ArmorClass1;
  hit_points: HitPoints;
  hit_dice: HitDice1;
  speed: Speed1;
  challenge_rating: ChallengeRating;
  abilities: Abilities;
  skills?: Skills1;
  senses: Senses;
  languages?: Languages1;
  attacks: Attacks1;
  special_abilities?: SpecialAbilities;
  damage_vulnerabilities?: DamageVulnerabilities;
  damage_resistances?: DamageResistances;
  damage_immunities?: DamageImmunities;
  condition_immunities?: ConditionImmunities;
  content_pack: ContentPack;
}
/**
 * Special ability or trait for a monster.
 */
export interface MonsterSpecialAbility {
  name: Name6;
  description: Description4;
}
/**
 * Dynamic scenario/location state for a game session.
 */
export interface ScenarioInstance {
  instance_id: InstanceId3;
  template_id: TemplateId2;
  created_at?: CreatedAt5;
  updated_at?: UpdatedAt3;
  sheet: ScenarioSheet;
  current_location_id?: CurrentLocationId2;
  location_states?: LocationStates;
  world_memories?: WorldMemories;
  last_world_message_index?: LastWorldMessageIndex;
  last_location_message_index?: LastLocationMessageIndex;
  last_npc_message_index?: LastNpcMessageIndex;
  tags?: Tags1;
}
/**
 * Complete enhanced scenario/adventure definition.
 */
export interface ScenarioSheet {
  id?: Id2;
  title: Title;
  description: Description5;
  starting_location_id: StartingLocationId;
  locations: Locations;
  encounters?: Encounters;
  random_encounters?: RandomEncounters;
  content_packs?: ContentPacks1;
}
/**
 * Enhanced location within a scenario.
 */
export interface ScenarioLocation {
  id: Id3;
  name: Name7;
  description: Description6;
  descriptions?: LocationDescriptions | null;
  notable_monsters?: NotableMonsters;
  encounter_ids?: EncounterIds;
  monster_ids?: MonsterIds;
  connections?: Connections;
  events?: Events;
  environmental_features?: EnvironmentalFeatures;
  secrets?: Secrets;
  loot_table?: LootTable;
  victory_conditions?: VictoryConditions;
  danger_level?: DangerLevel;
}
/**
 * Multiple description variants for different states.
 */
export interface LocationDescriptions {
  first_visit: FirstVisit;
  return_visit?: ReturnVisit;
  cleared?: Cleared;
  special_conditions?: SpecialConditions;
}
export interface SpecialConditions {
  [k: string]: string;
}
/**
 * Notable monster defined by the scenario with embedded stat block.
 */
export interface ScenarioMonster {
  id: Id4;
  display_name: DisplayName1;
  description?: Description7;
  monster: MonsterSheet;
}
/**
 * Connection between locations.
 */
export interface LocationConnection {
  to_location_id: ToLocationId1;
  description: Description8;
  direction?: Direction;
  requirements?: Requirements;
  is_visible?: IsVisible;
  is_accessible?: IsAccessible;
}
/**
 * Requirement to traverse a connection.
 */
export interface ConnectionRequirement {
  type: Type31;
  description: Description9;
  requirement_id?: RequirementId;
  dc?: Dc;
  is_met?: IsMet;
}
/**
 * Hidden secret in a location.
 */
export interface Secret {
  id: Id5;
  description: Description10;
  discovery_method: DiscoveryMethod;
  dc?: Dc1;
  reward?: Reward;
}
/**
 * Loot table entry for a location.
 */
export interface LootEntry {
  item_index: ItemIndex3;
  quantity_min?: QuantityMin;
  quantity_max?: QuantityMax;
  probability?: Probability;
  found?: Found;
  hidden?: Hidden;
  dc_to_find?: DcToFind;
}
export interface Encounters {
  [k: string]: Encounter;
}
/**
 * Encounter definition for a location.
 */
export interface Encounter {
  id: Id6;
  type: Type32;
  description: Description11;
  difficulty: Difficulty;
  participant_spawns?: ParticipantSpawns;
  dc?: Dc2;
  rewards?: Rewards;
}
/**
 * Participant spawn definition for encounters (monsters or NPCs).
 */
export interface EncounterParticipantSpawn {
  entity_type: EntityType;
  spawn_type: SpawnType;
  entity_id: EntityId2;
  faction: CombatFaction;
  quantity_min?: QuantityMin1;
  quantity_max?: QuantityMax1;
  probability?: Probability1;
}
export interface LocationStates {
  [k: string]: LocationState;
}
/**
 * Runtime state of a location.
 */
export interface LocationState {
  location_id: LocationId3;
  visited?: Visited;
  times_visited?: TimesVisited;
  danger_level?: DangerLevel1;
  completed_encounters?: CompletedEncounters;
  discovered_secrets?: DiscoveredSecrets;
  looted_items?: LootedItems;
  active_effects?: ActiveEffects;
  location_memories?: LocationMemories;
}
export interface LastLocationMessageIndex {
  [k: string]: number;
}
export interface LastNpcMessageIndex {
  [k: string]: number;
}
/**
 * In-game time tracking.
 */
export interface GameTime {
  day?: Day;
  hour?: Hour;
  minute?: Minute;
}
/**
 * State for managing party members (major NPCs that follow the player).
 *
 * Attributes:
 *     member_ids: List of NPC instance IDs that are in the party
 *     max_size: Maximum number of party members allowed (default 4)
 */
export interface PartyState {
  member_ids?: MemberIds;
  max_size?: MaxSize;
}
/**
 * Player-created journal entry with tags and timestamps.
 *
 * Player journal entries are editable notes that complement the auto-generated
 * memory system (world/location/NPC memories). They support manual and auto-linked
 * tags for filtering and organization.
 */
export interface PlayerJournalEntry {
  entry_id: EntryId;
  created_at?: CreatedAt6;
  updated_at?: UpdatedAt4;
  content: Content2;
  tags?: Tags2;
  location_id?: LocationId4;
  npc_ids?: NpcIds1;
  pinned?: Pinned;
}
/**
 * Chat message in game history (player, DM, or NPC).
 */
export interface Message17 {
  role: MessageRole;
  content: Content3;
  timestamp?: Timestamp13;
  agent_type?: AgentType1;
  location?: Location1;
  npcs_mentioned?: NpcsMentioned;
  combat_round?: CombatRound;
  combat_occurrence?: CombatOccurrence1;
  speaker_npc_id?: SpeakerNpcId;
  speaker_npc_name?: SpeakerNpcName;
}
/**
 * Game mechanics event that update the GameState.
 */
export interface GameEvent {
  event_type: GameEventType;
  timestamp?: Timestamp14;
  tool_name: ToolName4;
  parameters?: Parameters1;
  result?: Result1;
}
export interface Parameters1 {
  [k: string]:
    | string
    | number
    | number
    | boolean
    | {
        [k: string]: any;
      }
    | any[]
    | null;
}
export interface Result1 {
  [k: string]:
    | string
    | number
    | number
    | boolean
    | {
        [k: string]: any;
      }
    | any[]
    | null;
}
/**
 * Tracks state for ongoing NPC dialogue sessions.
 */
export interface DialogueSessionState {
  active?: Active;
  target_npc_ids?: TargetNpcIds;
  started_at?: StartedAt;
  last_interaction_at?: LastInteractionAt;
  mode?: DialogueSessionMode;
}
/**
 * Data for scenario info events.
 */
export interface ScenarioInfoData {
  timestamp?: Timestamp15;
  current_scenario: ScenarioSheet;
  available_scenarios: AvailableScenarios;
}
/**
 * Data for completion events.
 */
export interface CompleteData {
  timestamp?: Timestamp16;
  status: Status1;
}
