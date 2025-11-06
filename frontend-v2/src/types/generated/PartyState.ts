/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type MemberIds = string[];
export type MaxSize = number;

/**
 * State for managing party members (major NPCs that follow the player).
 *
 * Attributes:
 *     member_ids: List of NPC instance IDs that are in the party
 *     max_size: Maximum number of party members allowed (default 4)
 */
export interface PartyState {
  member_ids?: MemberIds;
  max_size?: MaxSize;
}
