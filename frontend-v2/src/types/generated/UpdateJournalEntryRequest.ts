/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Updated journal entry text content
 */
export type Content = string;
/**
 * Updated user-defined tags
 *
 * @maxItems 50
 */
export type Tags = string[];

/**
 * Request model for updating an existing journal entry.
 */
export interface UpdateJournalEntryRequest {
  content: Content;
  tags?: Tags;
}
