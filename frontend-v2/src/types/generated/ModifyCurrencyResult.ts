/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type OldGold = number;
export type OldSilver = number;
export type OldCopper = number;
export type NewGold = number;
export type NewSilver = number;
export type NewCopper = number;
export type ChangeGold = number;
export type ChangeSilver = number;
export type ChangeCopper = number;

export interface ModifyCurrencyResult {
  type?: Type;
  old_gold: OldGold;
  old_silver: OldSilver;
  old_copper: OldCopper;
  new_gold: NewGold;
  new_silver: NewSilver;
  new_copper: NewCopper;
  change_gold: ChangeGold;
  change_silver: ChangeSilver;
  change_copper: ChangeCopper;
}
