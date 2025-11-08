/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type OldHp = number;
export type NewHp = number;
export type Healing = number;
export type Time = string;

export interface ShortRestResult {
  type?: Type;
  old_hp: OldHp;
  new_hp: NewHp;
  healing: Healing;
  time: Time;
}
