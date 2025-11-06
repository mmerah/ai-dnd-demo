/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Level = number;
export type School = string;
export type CastingTime = string;
export type Range = string;
export type Duration = string;
export type Description = string;
export type HigherLevels = string | null;
export type ComponentsList = string[];
export type Material = string | null;
export type Ritual = boolean;
export type Concentration = boolean;
export type Classes = string[];
export type Subclasses = string[];
export type Size = number;
export type Type = string;
export type AttackType = string | null;
export type DcType = string;
export type DcSuccess = string | null;
export type Slot1 = string | null;
export type Slot2 = string | null;
export type Slot3 = string | null;
export type Slot4 = string | null;
export type Slot5 = string | null;
export type Slot6 = string | null;
export type Slot7 = string | null;
export type Slot8 = string | null;
export type Slot9 = string | null;
export type Slot11 = string | number | null;
export type Slot21 = string | number | null;
export type Slot31 = string | number | null;
export type Slot41 = string | number | null;
export type Slot51 = string | number | null;
export type Slot61 = string | number | null;
export type Slot71 = string | number | null;
export type Slot81 = string | number | null;
export type Slot91 = string | number | null;
export type Level1 = string | null;
export type Level5 = string | null;
export type Level11 = string | null;
export type Level17 = string | null;
export type ContentPack = string;

/**
 * Definition of a spell from data files (SRD-aligned).
 */
export interface SpellDefinition {
  index: Index;
  name: Name;
  level: Level;
  school: School;
  casting_time: CastingTime;
  range: Range;
  duration: Duration;
  description: Description;
  higher_levels?: HigherLevels;
  components_list?: ComponentsList;
  material?: Material;
  ritual?: Ritual;
  concentration?: Concentration;
  classes?: Classes;
  subclasses?: Subclasses;
  area_of_effect?: SpellAreaOfEffect | null;
  attack_type?: AttackType;
  dc?: SpellDC | null;
  damage_at_slot_level?: SpellDamageAtSlot | null;
  heal_at_slot_level?: SpellHealingAtSlot | null;
  damage_at_character_level?: SpellDamageAtLevel | null;
  content_pack: ContentPack;
}
export interface SpellAreaOfEffect {
  size: Size;
  type: Type;
}
export interface SpellDC {
  dc_type: DcType;
  dc_success?: DcSuccess;
}
/**
 * Spell damage scaling by slot level.
 */
export interface SpellDamageAtSlot {
  slot_1?: Slot1;
  slot_2?: Slot2;
  slot_3?: Slot3;
  slot_4?: Slot4;
  slot_5?: Slot5;
  slot_6?: Slot6;
  slot_7?: Slot7;
  slot_8?: Slot8;
  slot_9?: Slot9;
}
/**
 * Spell healing scaling by slot level.
 */
export interface SpellHealingAtSlot {
  slot_1?: Slot11;
  slot_2?: Slot21;
  slot_3?: Slot31;
  slot_4?: Slot41;
  slot_5?: Slot51;
  slot_6?: Slot61;
  slot_7?: Slot71;
  slot_8?: Slot81;
  slot_9?: Slot91;
}
/**
 * Cantrip damage scaling by character level.
 */
export interface SpellDamageAtLevel {
  level_1?: Level1;
  level_5?: Level5;
  level_11?: Level11;
  level_17?: Level17;
}
