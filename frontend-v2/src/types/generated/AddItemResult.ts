/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type ItemIndex = string;
export type Quantity = number;
export type TotalQuantity = number;

export interface AddItemResult {
  type?: Type;
  item_index: ItemIndex;
  quantity: Quantity;
  total_quantity: TotalQuantity;
}
