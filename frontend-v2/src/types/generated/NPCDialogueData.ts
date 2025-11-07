/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type NpcId = string;
export type NpcName = string;
export type Content = string;
export type Complete = boolean;

/**
 * Data for NPC dialogue events.
 */
export interface NPCDialogueData {
  timestamp?: Timestamp;
  npc_id: NpcId;
  npc_name: NpcName;
  content: Content;
  complete?: Complete;
}
