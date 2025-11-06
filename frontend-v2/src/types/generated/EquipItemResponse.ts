/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type GameId = string;
export type ItemIndex = string;
export type Equipped = boolean;
export type Slot = string | null;
export type NewArmorClass = number;

/**
 * Response model for equip/unequip operations.
 */
export interface EquipItemResponse {
  game_id: GameId;
  item_index: ItemIndex;
  equipped: Equipped;
  slot: Slot;
  new_armor_class: NewArmorClass;
}
