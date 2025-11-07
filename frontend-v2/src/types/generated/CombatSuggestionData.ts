/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
/**
 * Unique identifier for this suggestion
 */
export type SuggestionId = string;
/**
 * Instance ID of the NPC making the suggestion
 */
export type NpcId = string;
/**
 * Display name of the NPC
 */
export type NpcName = string;
/**
 * Simple description of the suggested action from NPC perspective
 */
export type ActionText = string;

/**
 * Data for combat suggestion events from allied NPCs.
 */
export interface CombatSuggestionData {
  timestamp?: Timestamp;
  suggestion: CombatSuggestion;
}
/**
 * Combat action suggestion from an allied NPC.
 *
 * Used when an allied NPC's turn comes up in combat to suggest an action
 * to the player for approval before execution.
 */
export interface CombatSuggestion {
  suggestion_id: SuggestionId;
  npc_id: NpcId;
  npc_name: NpcName;
  action_text: ActionText;
}
