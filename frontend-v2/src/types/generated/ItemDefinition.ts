/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
/**
 * Types of items in the game.
 */
export type ItemType = 'Weapon' | 'Armor' | 'Potion' | 'Ammunition' | 'Adventuring Gear' | 'Equipment Pack';
/**
 * Item rarity levels.
 */
export type ItemRarity = 'Common' | 'Uncommon' | 'Rare' | 'Very Rare' | 'Legendary' | 'Artifact' | 'Varies';
export type Weight = number;
export type Value = number;
export type Description = string;
/**
 * Subtypes for weapons and armor.
 */
export type ItemSubtype = 'Melee' | 'Ranged' | 'Light' | 'Medium' | 'Heavy' | 'Shield';
export type Damage = string;
export type DamageType = string;
export type Properties = string[];
export type ArmorClass = number;
export type DexBonus = boolean;
export type Contents = string[];
export type QuantityAvailable = number;
export type ContentPack = string;
/**
 * D&D 5e equipment slot types.
 */
export type EquipmentSlotType =
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
  | 'ammunition';
export type ValidSlots = EquipmentSlotType[];

/**
 * Definition of an item type from data files.
 */
export interface ItemDefinition {
  index: Index;
  name: Name;
  type: ItemType;
  rarity: ItemRarity;
  weight?: Weight;
  value?: Value;
  description: Description;
  subtype?: ItemSubtype | null;
  damage?: Damage;
  damage_type?: DamageType;
  properties?: Properties;
  armor_class?: ArmorClass;
  dex_bonus?: DexBonus;
  contents?: Contents;
  quantity_available?: QuantityAvailable;
  content_pack: ContentPack;
  valid_slots?: ValidSlots;
}
