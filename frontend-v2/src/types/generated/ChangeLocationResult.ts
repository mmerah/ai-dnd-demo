/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type LocationId = string;
export type LocationName = string;
export type Description = string | null;
export type Message = string;

export interface ChangeLocationResult {
  type?: Type;
  location_id: LocationId;
  location_name: LocationName;
  description: Description;
  message: Message;
}
