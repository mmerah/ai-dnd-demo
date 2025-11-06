/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Speed = number;
export type Size = string;
export type Languages = string[];
export type Description = string;
export type Traits = string[] | null;
export type Subraces = string[] | null;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type WeaponProficiencies = string[] | null;
export type ToolProficiencies = string[] | null;
export type LanguageOptions = string[] | null;
export type ContentPack = string;

export interface RaceDefinition {
  index: Index;
  name: Name;
  speed: Speed;
  size: Size;
  languages?: Languages;
  description: Description;
  traits?: Traits;
  subraces?: Subraces;
  ability_bonuses?: AbilityBonuses | null;
  weapon_proficiencies?: WeaponProficiencies;
  tool_proficiencies?: ToolProficiencies;
  language_options?: LanguageOptions;
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
