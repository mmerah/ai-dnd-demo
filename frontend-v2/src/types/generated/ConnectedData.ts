/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type GameId = string;
export type Status = 'connected';

/**
 * Data for connected event.
 */
export interface ConnectedData {
  timestamp?: Timestamp;
  game_id: GameId;
  status: Status;
}
