/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * True if entry was deleted, False if not found
 */
export type Success = boolean;
/**
 * ID of the deleted entry
 */
export type EntryId = string;

/**
 * Response model for deleting a journal entry.
 */
export interface DeleteJournalEntryResponse {
  success: Success;
  entry_id: EntryId;
}
