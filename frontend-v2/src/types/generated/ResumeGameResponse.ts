/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Unique identifier for the resumed game
 */
export type GameId = string;
/**
 * Resume status, typically 'resumed'
 */
export type Status = string;

/**
 * Response model for resuming a saved game.
 */
export interface ResumeGameResponse {
  game_id: GameId;
  status: Status;
}
