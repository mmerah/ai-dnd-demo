/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type Target = string;
export type Condition = string;
export type Removed = boolean;

export interface RemoveConditionResult {
  type?: Type;
  target: Target;
  condition: Condition;
  removed: Removed;
}
