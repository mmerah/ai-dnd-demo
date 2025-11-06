/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * ID of the removed game
 */
export type GameId = string;
/**
 * Removal status, typically 'removed'
 */
export type Status = string;

/**
 * Response model for removing a game.
 */
export interface RemoveGameResponse {
  game_id: GameId;
  status: Status;
}
