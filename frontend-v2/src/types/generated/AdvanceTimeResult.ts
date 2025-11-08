/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type OldTime = string;
export type NewTime = string;
export type MinutesAdvanced = number;

export interface AdvanceTimeResult {
  type?: Type;
  old_time: OldTime;
  new_time: NewTime;
  minutes_advanced: MinutesAdvanced;
}
