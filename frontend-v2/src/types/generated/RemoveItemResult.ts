/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type ItemIndex = string;
export type Quantity = number;
export type RemainingQuantity = number;

export interface RemoveItemResult {
  type?: Type;
  item_index: ItemIndex;
  quantity: Quantity;
  remaining_quantity: RemainingQuantity;
}
