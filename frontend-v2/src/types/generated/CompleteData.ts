/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type Status = 'success' | 'error';

/**
 * Data for completion events.
 */
export interface CompleteData {
  timestamp?: Timestamp;
  status: Status;
}
