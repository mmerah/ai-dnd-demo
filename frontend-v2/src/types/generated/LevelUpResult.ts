/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type Target = string;
export type OldLevel = number;
export type NewLevel = number;
export type OldMaxHp = number;
export type NewMaxHp = number;
export type HpIncrease = number;
export type Message = string;

export interface LevelUpResult {
  type?: Type;
  target: Target;
  old_level: OldLevel;
  new_level: NewLevel;
  old_max_hp: OldMaxHp;
  new_max_hp: NewMaxHp;
  hp_increase: HpIncrease;
  message: Message;
}
