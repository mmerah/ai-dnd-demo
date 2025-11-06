/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Unique identifier for the suggestion being accepted
 */
export type SuggestionId = string;
/**
 * Instance ID of the NPC who made the suggestion
 */
export type NpcId = string;
/**
 * Display name of the NPC
 */
export type NpcName = string;
/**
 * The suggested action text
 */
export type ActionText = string;

/**
 * Request model for accepting a combat suggestion from an allied NPC.
 */
export interface AcceptCombatSuggestionRequest {
  suggestion_id: SuggestionId;
  npc_id: NpcId;
  npc_name: NpcName;
  action_text: ActionText;
}
