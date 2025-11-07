/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type RoundNumber = number;
export type TurnIndex = number;
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
export type Participants = CombatParticipant[];
export type IsActive1 = boolean;
/**
 * Combat phase for explicit state tracking.
 */
export type CombatPhase = 'inactive' | 'starting' | 'active' | 'auto_ending' | 'ended';
export type CombatOccurrence = number;

/**
 * Data for combat update events.
 */
export interface CombatUpdateData {
  timestamp?: Timestamp;
  combat: CombatState;
}
/**
 * Combat encounter state.
 */
export interface CombatState {
  round_number?: RoundNumber;
  turn_index?: TurnIndex;
  participants?: Participants;
  is_active?: IsActive1;
  phase?: CombatPhase;
  combat_occurrence?: CombatOccurrence;
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
