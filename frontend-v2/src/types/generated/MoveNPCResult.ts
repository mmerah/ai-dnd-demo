/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type NpcId = string;
export type NpcName = string;
export type FromLocationId = string;
export type ToLocationId = string;
export type Message = string;

export interface MoveNPCResult {
  type?: Type;
  npc_id: NpcId;
  npc_name: NpcName;
  from_location_id: FromLocationId;
  to_location_id: ToLocationId;
  message: Message;
}
