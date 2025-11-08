/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type OldHp = number;
export type NewHp = number;
export type ConditionsRemoved = string[];
export type SpellSlotsRestored = boolean;
export type Time = string;

export interface LongRestResult {
  type?: Type;
  old_hp: OldHp;
  new_hp: NewHp;
  conditions_removed: ConditionsRemoved;
  spell_slots_restored: SpellSlotsRestored;
  time: Time;
}
