/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type ItemIndex = string;
export type Equipped = boolean;
export type Slot = string | null;
export type Message = string;

export interface EquipItemResult {
  type?: Type;
  item_index: ItemIndex;
  equipped: Equipped;
  slot?: Slot;
  message: Message;
}
