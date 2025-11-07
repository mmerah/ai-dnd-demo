/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type GameId = string;
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
export type Level = number;
export type ExperiencePoints = number;
export type Current = number;
export type Maximum = number;
export type Temporary = number;
export type Total = number;
export type Current1 = number;
export type Type = string;
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
export type Name = string;
export type AttackRollBonus = number;
export type Damage = string;
export type DamageType = string;
export type Range = string;
export type Properties = string[];
export type Type1 = string;
export type Reach = string;
export type Special = string;
export type Attacks = AttackAction[];
export type Conditions = string[];
export type ExhaustionLevel = number;
export type Inspiration = boolean;
export type Index1 = string;
export type Name1 = string | null;
/**
 * Types of items in the game.
 */
export type ItemType = 'Weapon' | 'Armor' | 'Potion' | 'Ammunition' | 'Adventuring Gear' | 'Equipment Pack';
export type Quantity = number;
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
export type Level1 = number;
export type Total1 = number;
export type Current2 = number;
export type SpellsPrepared = string[];
export type RitualSpells = string[];
export type TemplateId = string;
export type Id = string;
export type Name2 = string;
export type Race = string;
export type ClassIndex = string;
export type Subclass = string | null;
export type Subrace = string | null;
export type ContentPacks = string[];
export type StartingLevel = number;
export type Background = string;
export type Alignment = string;
export type StartingExperiencePoints = number;
export type Name3 = string;
export type Description = string;
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
export type Description1 = string;
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
export type LocationId = string | null;
export type NpcIds = string[];
export type EncounterId = string | null;
export type SinceTimestamp = string | null;
export type SinceMessageIndex = number | null;
export type NpcMemories = MemoryEntry[];
export type Npcs = NPCInstance[];
export type InstanceId2 = string;
export type CreatedAt4 = string;
export type UpdatedAt2 = string;
export type TemplateId1 = string;
export type Index2 = string;
export type Name4 = string;
export type Type2 = string;
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
export type Name5 = string;
export type Description2 = string;
export type SpecialAbilities = MonsterSpecialAbility[];
export type DamageVulnerabilities = string[];
export type DamageResistances = string[];
export type DamageImmunities = string[];
export type ConditionImmunities = string[];
export type ContentPack = string;
export type CurrentLocationId1 = string;
export type Monsters = MonsterInstance[];
export type ScenarioId = string;
export type ScenarioTitle = string;
export type InstanceId3 = string;
export type TemplateId2 = string;
export type CreatedAt5 = string;
export type UpdatedAt3 = string;
export type Id2 = string;
export type Title = string;
export type Description3 = string;
export type StartingLocationId = string;
export type Id3 = string;
export type Name6 = string;
export type Description4 = string;
export type FirstVisit = string;
export type ReturnVisit = string | null;
export type Cleared = string | null;
export type Id4 = string;
export type DisplayName1 = string;
export type Description5 = string | null;
export type NotableMonsters = ScenarioMonster[];
export type EncounterIds = string[];
export type MonsterIds = string[];
export type ToLocationId = string;
export type Description6 = string;
export type Direction = string | null;
export type Type3 = string;
export type Description7 = string;
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
export type Description8 = string;
export type DiscoveryMethod = string;
export type Dc1 = number | null;
export type Reward = string | null;
export type Secrets = Secret[];
export type ItemIndex = string;
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
export type Type4 = string;
export type Description9 = string;
export type Difficulty = string;
/**
 * Allowed runtime entity categories used in combat and lookups.
 */
export type EntityType = 'player' | 'npc' | 'monster';
/**
 * Type of entity to spawn. Repository is data/monsters, scenario data/scenarios/{id}/monsters.
 */
export type SpawnType = 'repository' | 'scenario';
export type EntityId = string;
/**
 * Faction for combat participants.
 */
export type CombatFaction = 'player' | 'ally' | 'enemy' | 'neutral';
export type QuantityMin1 = number;
export type QuantityMax1 = number;
export type Probability1 = number;
export type ParticipantSpawns = EncounterParticipantSpawn[];
export type Dc2 = number | null;
export type Rewards = string[];
export type RandomEncounters = Encounter[];
export type ContentPacks1 = string[];
export type CurrentLocationId2 = string;
export type LocationId1 = string;
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
export type Description10 = string;
export type Day = number;
export type Hour = number;
export type Minute = number;
export type RoundNumber = number;
export type TurnIndex = number;
export type EntityId1 = string;
export type Name7 = string;
export type Initiative = number | null;
export type IsPlayer = boolean;
export type IsActive = boolean;
export type Participants = CombatParticipant[];
export type IsActive1 = boolean;
/**
 * Combat phase for explicit state tracking.
 */
export type CombatPhase = 'inactive' | 'starting' | 'active' | 'auto_ending' | 'ended';
export type CombatOccurrence = number;
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
export type Content = string;
/**
 * User-defined and auto-linked tags
 *
 * @maxItems 50
 */
export type Tags2 = string[];
/**
 * Auto-linked location ID at time of creation
 */
export type LocationId2 = string | null;
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
export type Content1 = string;
export type Timestamp1 = string;
/**
 * Types of specialized agents.
 */
export type AgentType = 'narrative' | 'combat' | 'summarizer' | 'npc' | 'player' | 'tool_suggestor';
export type Location1 = string | null;
export type NpcsMentioned = string[];
export type CombatRound = number | null;
export type CombatOccurrence1 = number | null;
export type SpeakerNpcId = string | null;
export type SpeakerNpcName = string | null;
export type ConversationHistory = Message[];
/**
 * Types of game events.
 */
export type GameEventType = 'tool_call' | 'tool_result';
export type Timestamp2 = string;
export type ToolName = string;
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
export type AgentType1 = 'narrative' | 'combat' | 'summarizer' | 'npc' | 'player' | 'tool_suggestor';
export type SessionNumber = number;
export type TotalPlayTimeMinutes = number;

/**
 * Data for complete game state update events.
 */
export interface GameUpdateData {
  timestamp?: Timestamp;
  game_state: GameState;
}
/**
 * Complete game state for a D&D session.
 */
export interface GameState {
  game_id: GameId;
  created_at?: CreatedAt;
  last_saved?: LastSaved;
  character: CharacterInstance;
  npcs?: Npcs;
  monsters?: Monsters;
  scenario_id: ScenarioId;
  scenario_title: ScenarioTitle;
  scenario_instance: ScenarioInstance;
  content_packs?: ContentPacks2;
  location?: Location;
  description?: Description10;
  game_time?: GameTime;
  combat?: CombatState;
  party?: PartyState;
  story_notes?: StoryNotes;
  player_journal_entries?: PlayerJournalEntries;
  conversation_history?: ConversationHistory;
  game_events?: GameEvents;
  dialogue_session?: DialogueSessionState;
  active_agent?: AgentType1;
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
  level?: Level;
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
  total: Total;
  current: Current1;
  type: Type;
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
  name: Name;
  attack_roll_bonus: AttackRollBonus;
  damage: Damage;
  damage_type: DamageType;
  range?: Range;
  properties?: Properties;
  type?: Type1;
  reach?: Reach;
  special?: Special;
}
/**
 * Item instance in inventory.
 */
export interface InventoryItem {
  index: Index1;
  name?: Name1;
  item_type?: ItemType | null;
  quantity?: Quantity;
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
  level: Level1;
  total: Total1;
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
  name: Name2;
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
  name: Name3;
  description: Description;
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
  description: Description1;
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
  location_id?: LocationId;
  npc_ids?: NpcIds;
  encounter_id?: EncounterId;
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
  name: Name4;
  type: Type2;
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
  name: Name5;
  description: Description2;
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
  description: Description3;
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
  name: Name6;
  description: Description4;
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
  description?: Description5;
  monster: MonsterSheet;
}
/**
 * Connection between locations.
 */
export interface LocationConnection {
  to_location_id: ToLocationId;
  description: Description6;
  direction?: Direction;
  requirements?: Requirements;
  is_visible?: IsVisible;
  is_accessible?: IsAccessible;
}
/**
 * Requirement to traverse a connection.
 */
export interface ConnectionRequirement {
  type: Type3;
  description: Description7;
  requirement_id?: RequirementId;
  dc?: Dc;
  is_met?: IsMet;
}
/**
 * Hidden secret in a location.
 */
export interface Secret {
  id: Id5;
  description: Description8;
  discovery_method: DiscoveryMethod;
  dc?: Dc1;
  reward?: Reward;
}
/**
 * Loot table entry for a location.
 */
export interface LootEntry {
  item_index: ItemIndex;
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
  type: Type4;
  description: Description9;
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
  entity_id: EntityId;
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
  location_id: LocationId1;
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
 * Combat encounter state.
 */
export interface CombatState {
  round_number?: RoundNumber;
  turn_index?: TurnIndex;
  participants?: Participants;
  is_active?: IsActive1;
  phase?: CombatPhase;
  combat_occurrence?: CombatOccurrence;
}
/**
 * Participant in combat with initiative and stable entity reference.
 */
export interface CombatParticipant {
  entity_id: EntityId1;
  entity_type: EntityType;
  faction: CombatFaction;
  name: Name7;
  initiative?: Initiative;
  is_player?: IsPlayer;
  is_active?: IsActive;
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
  content: Content;
  tags?: Tags2;
  location_id?: LocationId2;
  npc_ids?: NpcIds1;
  pinned?: Pinned;
}
/**
 * Chat message in game history (player, DM, or NPC).
 */
export interface Message {
  role: MessageRole;
  content: Content1;
  timestamp?: Timestamp1;
  agent_type?: AgentType;
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
  timestamp?: Timestamp2;
  tool_name: ToolName;
  parameters?: Parameters;
  result?: Result;
}
export interface Parameters {
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
export interface Result {
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
