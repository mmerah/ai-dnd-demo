/**
 * ItemList Component
 *
 * Displays the character's inventory items with equip functionality.
 * Shows equipped status and provides slot selector for equippable items.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div, button, select, option } from '../../utils/dom.js';
import type { InventoryItem, EquipmentSlots } from '../../types/generated/GameState.js';
import {
  getValidSlotsForItem,
  isItemEquippable,
  formatSlotName,
  type EquipmentSlot,
} from '../../utils/itemSlotValidation.js';

export interface ItemListProps {
  items: InventoryItem[];
  equipmentSlots: EquipmentSlots;
  onEquip: (itemIndex: string, slot: EquipmentSlot | null) => void;
  initiallyCollapsed?: boolean;
}

/**
 * Item list component with equip functionality
 */
export class ItemList extends Component<ItemListProps> {
  private collapsibleSection: CollapsibleSection | null = null;

  constructor(props: ItemListProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const content = div({ class: 'item-list__content' });

    if (this.props.items.length === 0) {
      const empty = div({ class: 'item-list__empty' }, 'No items in inventory');
      content.appendChild(empty);
    } else {
      // Note: Weight information is not available in InventoryItem (runtime state).
      // Weight would need to be fetched from item catalog definitions if needed.
      // For now, we skip total weight display as it would be inaccurate.

      // Get equipped item indexes
      const equippedItemIndexes = new Set(
        Object.values(this.props.equipmentSlots).filter((val): val is string => !!val)
      );

      // Items list
      const itemsContainer = div({ class: 'item-list__items' });

      for (const item of this.props.items) {
        const itemRow = div({ class: 'item-row' });

        // Left side: name and quantity
        const nameContainer = div({ class: 'item-row__name-container' });
        const name = div({ class: 'item-row__name' }, item.name ?? item.index);
        const quantity = div({ class: 'item-row__quantity' }, `×${item.quantity ?? 1}`);
        nameContainer.appendChild(name);
        nameContainer.appendChild(quantity);
        itemRow.appendChild(nameContainer);

        // Check if item is equipped
        const isEquipped = equippedItemIndexes.has(item.index);

        if (isEquipped) {
          // Show where it's equipped
          const equippedSlots = Object.entries(this.props.equipmentSlots)
            .filter(([_, index]) => index === item.index)
            .map(([slot, _]) => formatSlotName(slot as EquipmentSlot));

          const status = div(
            { class: 'item-row__equipped-status' },
            `Equipped (${equippedSlots.join(', ')})`
          );
          itemRow.appendChild(status);
        } else if (isItemEquippable(item)) {
          // Show equip controls
          const actions = div({ class: 'item-row__actions' });

          // Slot selector dropdown
          const validSlots = getValidSlotsForItem(item);
          const slotSelect = select({ class: 'item-row__slot-select' });

          // Add "Auto" option (null slot = auto-select)
          slotSelect.appendChild(option('Auto', { value: '' }));

          // Add valid slot options
          for (const slot of validSlots) {
            slotSelect.appendChild(option(formatSlotName(slot), { value: slot }));
          }

          actions.appendChild(slotSelect);

          // Equip button
          const equipBtn = button('Equip', {
            class: 'item-row__equip-btn',
            onclick: () => {
              const selectedSlot = slotSelect.value as EquipmentSlot | '';
              this.props.onEquip(item.index, selectedSlot || null);
            },
          });
          actions.appendChild(equipBtn);

          itemRow.appendChild(actions);
        }

        itemsContainer.appendChild(itemRow);
      }

      content.appendChild(itemsContainer);
    }

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Inventory',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [content],
    });

    const container = div({ class: 'item-list' });
    this.collapsibleSection.mount(container);

    return container;
  }

  override onUnmount(): void {
    if (this.collapsibleSection) {
      this.collapsibleSection.unmount();
      this.collapsibleSection = null;
    }
  }
}
