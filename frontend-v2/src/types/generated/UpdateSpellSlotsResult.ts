/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type Target = string;
export type Level = number;
export type OldSlots = number;
export type NewSlots = number;
export type MaxSlots = number;
export type Change = number;

export interface UpdateSpellSlotsResult {
  type?: Type;
  target: Target;
  level: Level;
  old_slots: OldSlots;
  new_slots: NewSlots;
  max_slots: MaxSlots;
  change: Change;
}
