/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type RollType = string;
export type Dice = string;
export type Modifier = number;
export type Rolls = number[];
export type Total = number;
export type Ability = string | null;
export type Skill = string | null;
export type Critical = boolean | null;

export interface RollDiceResult {
  type: Type;
  roll_type: RollType;
  dice: Dice;
  modifier: Modifier;
  rolls: Rolls;
  total: Total;
  ability?: Ability;
  skill?: Skill;
  critical?: Critical;
}
