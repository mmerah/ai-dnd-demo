/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type ParentRace = string;
export type Description = string;
export type Traits = string[] | null;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type WeaponProficiencies = string[] | null;
export type ToolProficiencies = string[] | null;
export type ContentPack = string;

export interface SubraceDefinition {
  index: Index;
  name: Name;
  parent_race: ParentRace;
  description: Description;
  traits?: Traits;
  ability_bonuses?: AbilityBonuses | null;
  weapon_proficiencies?: WeaponProficiencies;
  tool_proficiencies?: ToolProficiencies;
  content_pack: ContentPack;
}
/**
 * Ability score bonuses for races and subraces.
 *
 * All fields are optional with default 0.
 */
export interface AbilityBonuses {
  STR?: Str;
  DEX?: Dex;
  CON?: Con;
  INT?: Int;
  WIS?: Wis;
  CHA?: Cha;
}
