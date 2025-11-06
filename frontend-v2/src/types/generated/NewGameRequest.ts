/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * ID of the character to play
 */
export type CharacterId = string;
/**
 * ID of the scenario to play
 */
export type ScenarioId = string;
/**
 * Additional content packs to use with scenario
 */
export type ContentPacks = string[] | null;

/**
 * Request model for creating a new game.
 */
export interface NewGameRequest {
  character_id: CharacterId;
  scenario_id: ScenarioId;
  content_packs?: ContentPacks;
}
