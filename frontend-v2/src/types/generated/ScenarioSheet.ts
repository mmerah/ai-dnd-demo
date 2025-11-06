/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Id = string;
export type Title = string;
export type Description = string;
export type StartingLocationId = string;
export type Id1 = string;
export type Name = string;
export type Description1 = string;
export type FirstVisit = string;
export type ReturnVisit = string | null;
export type Cleared = string | null;
export type Id2 = string;
export type DisplayName = string;
export type Description2 = string | null;
export type Index = string;
export type Name1 = string;
export type Type = string;
export type Size = string;
export type Alignment = string;
export type ArmorClass = number;
export type Current = number;
export type Maximum = number;
export type Temporary = number;
export type HitDice = string;
export type Speed = string;
export type ChallengeRating = number;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type Index1 = string;
export type Value = number;
export type Skills = SkillValue[];
export type Senses = string;
export type Languages = string[];
export type Name2 = string;
export type AttackRollBonus = number;
export type Damage = string;
export type DamageType = string;
export type Range = string;
export type Properties = string[];
export type Type1 = string;
export type Reach = string;
export type Special = string;
export type Attacks = AttackAction[];
export type Name3 = string;
export type Description3 = string;
export type SpecialAbilities = MonsterSpecialAbility[];
export type DamageVulnerabilities = string[];
export type DamageResistances = string[];
export type DamageImmunities = string[];
export type ConditionImmunities = string[];
export type ContentPack = string;
export type NotableMonsters = ScenarioMonster[];
export type EncounterIds = string[];
export type MonsterIds = string[];
export type ToLocationId = string;
export type Description4 = string;
export type Direction = string | null;
export type Type2 = string;
export type Description5 = string;
export type RequirementId = string | null;
export type Dc = number | null;
export type IsMet = boolean;
export type Requirements = ConnectionRequirement[];
export type IsVisible = boolean;
export type IsAccessible = boolean;
export type Connections = LocationConnection[];
export type Events = string[];
export type EnvironmentalFeatures = string[];
export type Id3 = string;
export type Description6 = string;
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
export type Id4 = string;
export type Type3 = string;
export type Description7 = string;
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
export type ContentPacks = string[];

/**
 * Complete enhanced scenario/adventure definition.
 */
export interface ScenarioSheet {
  id?: Id;
  title: Title;
  description: Description;
  starting_location_id: StartingLocationId;
  locations: Locations;
  encounters?: Encounters;
  random_encounters?: RandomEncounters;
  content_packs?: ContentPacks;
}
/**
 * Enhanced location within a scenario.
 */
export interface ScenarioLocation {
  id: Id1;
  name: Name;
  description: Description1;
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
  id: Id2;
  display_name: DisplayName;
  description?: Description2;
  monster: MonsterSheet;
}
/**
 * Minimal monster stat block (template).
 */
export interface MonsterSheet {
  index: Index;
  name: Name1;
  type: Type;
  size: Size;
  alignment: Alignment;
  armor_class: ArmorClass;
  hit_points: HitPoints;
  hit_dice: HitDice;
  speed: Speed;
  challenge_rating: ChallengeRating;
  abilities: Abilities;
  skills?: Skills;
  senses: Senses;
  languages?: Languages;
  attacks: Attacks;
  special_abilities?: SpecialAbilities;
  damage_vulnerabilities?: DamageVulnerabilities;
  damage_resistances?: DamageResistances;
  damage_immunities?: DamageImmunities;
  condition_immunities?: ConditionImmunities;
  content_pack: ContentPack;
}
export interface HitPoints {
  current: Current;
  maximum: Maximum;
  temporary?: Temporary;
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
/**
 * Runtime skill value bound to a skill index.
 */
export interface SkillValue {
  index: Index1;
  value: Value;
}
export interface AttackAction {
  name: Name2;
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
 * Special ability or trait for a monster.
 */
export interface MonsterSpecialAbility {
  name: Name3;
  description: Description3;
}
/**
 * Connection between locations.
 */
export interface LocationConnection {
  to_location_id: ToLocationId;
  description: Description4;
  direction?: Direction;
  requirements?: Requirements;
  is_visible?: IsVisible;
  is_accessible?: IsAccessible;
}
/**
 * Requirement to traverse a connection.
 */
export interface ConnectionRequirement {
  type: Type2;
  description: Description5;
  requirement_id?: RequirementId;
  dc?: Dc;
  is_met?: IsMet;
}
/**
 * Hidden secret in a location.
 */
export interface Secret {
  id: Id3;
  description: Description6;
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
  id: Id4;
  type: Type3;
  description: Description7;
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
