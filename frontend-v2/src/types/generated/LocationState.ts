/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type LocationId = string;
export type Visited = boolean;
export type TimesVisited = number;
/**
 * Danger level of a location.
 */
export type DangerLevel = 'safe' | 'low' | 'moderate' | 'high' | 'extreme' | 'cleared';
export type CompletedEncounters = string[];
export type DiscoveredSecrets = string[];
export type LootedItems = string[];
export type ActiveEffects = string[];
export type CreatedAt = string;
/**
 * Scope of a recorded memory.
 */
export type MemorySource = 'location' | 'npc' | 'world';
export type Summary = string;
export type Tags = string[];
export type LocationId1 = string | null;
export type NpcIds = string[];
export type EncounterId = string | null;
export type SinceTimestamp = string | null;
export type SinceMessageIndex = number | null;
export type LocationMemories = MemoryEntry[];

/**
 * Runtime state of a location.
 */
export interface LocationState {
  location_id: LocationId;
  visited?: Visited;
  times_visited?: TimesVisited;
  danger_level?: DangerLevel;
  completed_encounters?: CompletedEncounters;
  discovered_secrets?: DiscoveredSecrets;
  looted_items?: LootedItems;
  active_effects?: ActiveEffects;
  location_memories?: LocationMemories;
}
/**
 * Append-only memory snapshot summarizing recent events.
 */
export interface MemoryEntry {
  created_at?: CreatedAt;
  source: MemorySource;
  summary: Summary;
  tags?: Tags;
  location_id?: LocationId1;
  npc_ids?: NpcIds;
  encounter_id?: EncounterId;
  since_timestamp?: SinceTimestamp;
  since_message_index?: SinceMessageIndex;
}
