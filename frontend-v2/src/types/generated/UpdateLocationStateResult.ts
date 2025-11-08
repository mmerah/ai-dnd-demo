/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type LocationId = string;
export type Updates = string[];
export type Message = string;

export interface UpdateLocationStateResult {
  type?: Type;
  location_id: LocationId;
  updates: Updates;
  message: Message;
}
