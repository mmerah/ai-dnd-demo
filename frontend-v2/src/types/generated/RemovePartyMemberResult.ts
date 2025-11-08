/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type NpcId = string;
export type NpcName = string;
export type PartySize = number;
export type Message = string;

export interface RemovePartyMemberResult {
  type?: Type;
  npc_id: NpcId;
  npc_name: NpcName;
  party_size: PartySize;
  message: Message;
}
