/**
 * EquipmentSlots Component
 *
 * Displays equipped items with interactive unequip functionality.
 * Clicking the unequip button (×) removes the item from the slot.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div, button } from '../../utils/dom.js';
import type { EquipmentSlots as EquipmentSlotsType, InventoryItem } from '../../types/generated/GameState.js';
import type { EquipmentSlot } from '../../utils/itemSlotValidation.js';

export interface EquipmentSlotsProps {
  equipment: EquipmentSlotsType;
  inventory: InventoryItem[];
  onUnequip: (slot: EquipmentSlot) => void;
  initiallyCollapsed?: boolean;
}

/**
 * Equipment slots component with interactive unequip buttons
 */
export class EquipmentSlots extends Component<EquipmentSlotsProps> {
  private collapsibleSection: CollapsibleSection | null = null;

  constructor(props: EquipmentSlotsProps) {
    super(props);
  }

  protected render(): HTMLElement {

    const slots: Array<{
      key: EquipmentSlot;
      label: string;
      value: string | null | undefined;
    }> = [
      { key: 'main_hand', label: '⚔️ Main Hand', value: this.props.equipment.main_hand },
      { key: 'off_hand', label: '🛡️ Off Hand', value: this.props.equipment.off_hand },
      { key: 'chest', label: '🛡️ Chest', value: this.props.equipment.chest },
      { key: 'head', label: '👑 Head', value: this.props.equipment.head },
      { key: 'hands', label: '🧤 Hands', value: this.props.equipment.hands },
      { key: 'feet', label: '👢 Feet', value: this.props.equipment.feet },
    ];

    const slotsList = div({ class: 'equipment-slots-list' });

    for (const slot of slots) {
      const slotRow = div({ class: 'equipment-slot' });

      const label = div({ class: 'equipment-slot__label' }, slot.label);

      if (slot.value) {
        // Find item in inventory to get display name
        const item = this.props.inventory.find(it => it.index === slot.value);
        const displayName = item?.name || slot.value;

        // Equipped item container
        const valueContainer = div({ class: 'equipment-slot__value-container' });

        // Item name
        const itemName = div({ class: 'equipment-slot__value' }, displayName);
        valueContainer.appendChild(itemName);

        // Unequip button
        const unequipBtn = button('×', {
          class: 'equipment-slot__unequip-btn',
          title: 'Unequip',
          onclick: (e) => {
            e.stopPropagation();
            this.props.onUnequip(slot.key);
          },
        });
        valueContainer.appendChild(unequipBtn);

        slotRow.appendChild(label);
        slotRow.appendChild(valueContainer);
      } else {
        // Empty slot
        const value = div(
          { class: 'equipment-slot__value equipment-slot__value--empty' },
          'None'
        );
        slotRow.appendChild(label);
        slotRow.appendChild(value);
      }

      slotsList.appendChild(slotRow);
    }

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Equipment',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [slotsList],
    });

    const container = div({ class: 'equipment-slots' });
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
