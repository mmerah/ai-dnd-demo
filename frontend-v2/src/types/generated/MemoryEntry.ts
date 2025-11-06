/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type CreatedAt = string;
/**
 * Scope of a recorded memory.
 */
export type MemorySource = 'location' | 'npc' | 'world';
export type Summary = string;
export type Tags = string[];
export type LocationId = string | null;
export type NpcIds = string[];
export type EncounterId = string | null;
export type SinceTimestamp = string | null;
export type SinceMessageIndex = number | null;

/**
 * Append-only memory snapshot summarizing recent events.
 */
export interface MemoryEntry {
  created_at?: CreatedAt;
  source: MemorySource;
  summary: Summary;
  tags?: Tags;
  location_id?: LocationId;
  npc_ids?: NpcIds;
  encounter_id?: EncounterId;
  since_timestamp?: SinceTimestamp;
  since_message_index?: SinceMessageIndex;
}
