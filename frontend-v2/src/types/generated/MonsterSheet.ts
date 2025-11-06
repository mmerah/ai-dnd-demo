/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
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
export type Name1 = string;
export type AttackRollBonus = number;
export type Damage = string;
export type DamageType = string;
export type Range = string;
export type Properties = string[];
export type Type1 = string;
export type Reach = string;
export type Special = string;
export type Attacks = AttackAction[];
export type Name2 = string;
export type Description = string;
export type SpecialAbilities = MonsterSpecialAbility[];
export type DamageVulnerabilities = string[];
export type DamageResistances = string[];
export type DamageImmunities = string[];
export type ConditionImmunities = string[];
export type ContentPack = string;

/**
 * Minimal monster stat block (template).
 */
export interface MonsterSheet {
  index: Index;
  name: Name;
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
  name: Name1;
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
  name: Name2;
  description: Description;
}
