/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Unique identifier for the journal entry
 */
export type EntryId = string;
/**
 * Entry creation timestamp
 */
export type CreatedAt = string;
/**
 * Last modification timestamp
 */
export type UpdatedAt = string;
/**
 * Journal entry text content
 */
export type Content = string;
/**
 * User-defined and auto-linked tags
 *
 * @maxItems 50
 */
export type Tags = string[];
/**
 * Auto-linked location ID at time of creation
 */
export type LocationId = string | null;
/**
 * Auto-linked NPC IDs if dialogue active
 */
export type NpcIds = string[];
/**
 * Whether this entry is pinned to the top of the list
 */
export type Pinned = boolean;

/**
 * Response model for creating a journal entry.
 */
export interface CreateJournalEntryResponse {
  entry: PlayerJournalEntry;
}
/**
 * The created journal entry
 */
export interface PlayerJournalEntry {
  entry_id: EntryId;
  created_at?: CreatedAt;
  updated_at?: UpdatedAt;
  content: Content;
  tags?: Tags;
  location_id?: LocationId;
  npc_ids?: NpcIds;
  pinned?: Pinned;
}
