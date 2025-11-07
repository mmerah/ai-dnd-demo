/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type Error = string;
export type Type = string | null;

/**
 * Data for error events.
 */
export interface ErrorData {
  timestamp?: Timestamp;
  error: Error;
  type?: Type;
}
