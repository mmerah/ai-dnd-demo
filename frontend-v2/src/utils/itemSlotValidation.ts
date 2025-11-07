/**
 * Item slot validation utilities
 *
 * Determines which equipment slots are valid for different item types.
 * Based on D&D 5e equipment rules and game-specific constraints.
 */

import type { InventoryItem } from '../types/generated/GameState.js';

/**
 * Valid equipment slot names
 */
export type EquipmentSlot =
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

/**
 * Determine valid slots for an item based on its type and properties.
 *
 * @param item - The inventory item to check
 * @returns Array of valid slot names
 */
export function getValidSlotsForItem(item: InventoryItem): EquipmentSlot[] {
  const type = item.item_type;
  const index = item.index;
  const name = (item.name || index).toLowerCase();

  // Armor type items
  if (type === 'Armor') {
    // Shields can go in either hand
    if (index.includes('shield') || name.includes('shield')) {
      return ['off_hand', 'main_hand'];
    }
    // Body armor goes in chest slot
    if (
      name.includes('armor') ||
      name.includes('mail') ||
      name.includes('plate') ||
      name.includes('leather')
    ) {
      return ['chest'];
    }
    // Default armor to chest
    return ['chest'];
  }

  // Weapon type items
  if (type === 'Weapon') {
    // Two-handed weapons only in main hand
    if (
      name.includes('two-handed') ||
      name.includes('longbow') ||
      name.includes('shortbow') ||
      name.includes('crossbow') ||
      name.includes('greatsword') ||
      name.includes('greataxe') ||
      name.includes('maul') ||
      name.includes('pike') ||
      name.includes('glaive') ||
      name.includes('halberd')
    ) {
      return ['main_hand'];
    }
    // Versatile and one-handed weapons can go in either hand
    return ['main_hand', 'off_hand'];
  }

  // Ammunition
  if (type === 'Ammunition') {
    return ['ammunition'];
  }

  // Special item types based on index patterns
  if (index.startsWith('ring-') || name.includes('ring')) {
    return ['ring_1', 'ring_2'];
  }

  if (index.startsWith('amulet-') || index.startsWith('necklace-') || name.includes('amulet')) {
    return ['neck'];
  }

  if (index.startsWith('cloak-') || index.startsWith('cape-') || name.includes('cloak')) {
    return ['back'];
  }

  if (index.startsWith('boots-') || name.includes('boots')) {
    return ['feet'];
  }

  if (index.startsWith('gloves-') || name.includes('gloves') || name.includes('gauntlet')) {
    return ['hands'];
  }

  if (
    index.startsWith('helmet-') ||
    index.startsWith('hat-') ||
    name.includes('helmet') ||
    name.includes('hat')
  ) {
    return ['head'];
  }

  if (index.startsWith('belt-') || name.includes('belt')) {
    return ['waist'];
  }

  // No valid slots for this item type
  return [];
}

/**
 * Check if an item is equippable (has at least one valid slot)
 *
 * @param item - The inventory item to check
 * @returns True if the item can be equipped
 */
export function isItemEquippable(item: InventoryItem): boolean {
  const validSlots = getValidSlotsForItem(item);
  return validSlots.length > 0;
}

/**
 * Format a slot name for display (e.g., "main_hand" -> "Main Hand")
 *
 * @param slot - The slot name
 * @returns Formatted slot name
 */
export function formatSlotName(slot: EquipmentSlot): string {
  return slot
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
