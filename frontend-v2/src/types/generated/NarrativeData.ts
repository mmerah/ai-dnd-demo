/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type Word = string | null;
export type Complete = boolean | null;
export type Start = boolean | null;
export type Content = string | null;

/**
 * Data for narrative streaming events.
 */
export interface NarrativeData {
  timestamp?: Timestamp;
  word?: Word;
  complete?: Complete;
  start?: Start;
  content?: Content;
}
