/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Index of the item in inventory
 */
export type ItemIndex = string;
/**
 * Instance ID of entity
 */
export type EntityId = string;
/**
 * Type of entity ('player' or 'npc')
 */
export type EntityType = 'player' | 'npc';
/**
 * Target equipment slot. Auto-selects if not specified.
 */
export type Slot =
  | (
      | 'head'
      | 'neck'
      | 'chest'
      | 'hands'
      | 'feet'
      | 'waist'
      | 'main_hand'
      | 'off_hand'
      | 'ring_1'
      | 'ring_2'
      | 'back'
      | 'ammunition'
    )
  | null;
/**
 * True to unequip from slots
 */
export type Unequip = boolean;

/**
 * Request model to equip or unequip a specific inventory item for an entity (player or NPC).
 */
export interface EquipItemRequest {
  item_index: ItemIndex;
  entity_id: EntityId;
  entity_type: EntityType;
  slot?: Slot;
  unequip?: Unequip;
}
