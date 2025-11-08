/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type RoundNumber = number;
export type EntityId = string;
/**
 * Allowed runtime entity categories used in combat and lookups.
 */
export type EntityType = 'player' | 'npc' | 'monster';
/**
 * Faction for combat participants.
 */
export type CombatFaction = 'player' | 'ally' | 'enemy' | 'neutral';
export type Name = string;
export type Initiative = number | null;
export type IsPlayer = boolean;
export type IsActive = boolean;
export type Message = string;

export interface NextTurnResult {
  type?: Type;
  round_number: RoundNumber;
  current_turn: CombatParticipant | null;
  message: Message;
}
/**
 * Participant in combat with initiative and stable entity reference.
 */
export interface CombatParticipant {
  entity_id: EntityId;
  entity_type: EntityType;
  faction: CombatFaction;
  name: Name;
  initiative?: Initiative;
  is_player?: IsPlayer;
  is_active?: IsActive;
}
