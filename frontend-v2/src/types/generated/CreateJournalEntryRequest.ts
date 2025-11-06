/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Journal entry text content
 */
export type Content = string;
/**
 * User-defined tags (comma-separated)
 *
 * @maxItems 50
 */
export type Tags = string[];

/**
 * Request model for creating a new journal entry.
 */
export interface CreateJournalEntryRequest {
  content: Content;
  tags?: Tags;
}
