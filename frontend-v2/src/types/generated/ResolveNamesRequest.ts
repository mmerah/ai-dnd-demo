/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Game ID for content pack scoping
 */
export type GameId = string;
/**
 * Item indexes to resolve
 */
export type Items = string[] | null;
/**
 * Spell indexes to resolve
 */
export type Spells = string[] | null;
/**
 * Monster indexes to resolve
 */
export type Monsters = string[] | null;
/**
 * Class indexes to resolve
 */
export type Classes = string[] | null;
/**
 * Race indexes to resolve
 */
export type Races = string[] | null;
/**
 * Alignment indexes to resolve
 */
export type Alignments = string[] | null;
/**
 * Background indexes to resolve
 */
export type Backgrounds = string[] | null;
/**
 * Feat indexes to resolve
 */
export type Feats = string[] | null;
/**
 * Feature indexes to resolve
 */
export type Features = string[] | null;
/**
 * Trait indexes to resolve
 */
export type Traits = string[] | null;
/**
 * Skill indexes to resolve
 */
export type Skills = string[] | null;
/**
 * Condition indexes to resolve
 */
export type Conditions = string[] | null;
/**
 * Language indexes to resolve
 */
export type Languages = string[] | null;
/**
 * Damage Types indexes to resolve
 */
export type DamageTypes = string[] | null;
/**
 * Magic Schools indexes to resolve
 */
export type MagicSchools = string[] | null;
/**
 * Subclasses indexes to resolve
 */
export type Subclasses = string[] | null;
/**
 * Subraces indexes to resolve
 */
export type Subraces = string[] | null;
/**
 * Weapon Properties indexes to resolve
 */
export type WeaponProperties = string[] | null;

/**
 * Request model for resolving catalog names from indexes.
 */
export interface ResolveNamesRequest {
  game_id: GameId;
  items?: Items;
  spells?: Spells;
  monsters?: Monsters;
  classes?: Classes;
  races?: Races;
  alignments?: Alignments;
  backgrounds?: Backgrounds;
  feats?: Feats;
  features?: Features;
  traits?: Traits;
  skills?: Skills;
  conditions?: Conditions;
  languages?: Languages;
  damage_types?: DamageTypes;
  magic_schools?: MagicSchools;
  subclasses?: Subclasses;
  subraces?: Subraces;
  weapon_properties?: WeaponProperties;
}
