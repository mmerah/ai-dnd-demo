/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type Target = string;
export type OldHp = number;
export type NewHp = number;
export type MaxHp = number;
export type Amount = number;
export type DamageType = string;
export type IsHealing = boolean;
export type IsUnconscious = boolean;

export interface UpdateHPResult {
  type?: Type;
  target: Target;
  old_hp: OldHp;
  new_hp: NewHp;
  max_hp: MaxHp;
  amount: Amount;
  damage_type: DamageType;
  is_healing: IsHealing;
  is_unconscious: IsUnconscious;
}
