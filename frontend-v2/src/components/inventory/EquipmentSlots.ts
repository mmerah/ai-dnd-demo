/**
 * EquipmentSlots Component
 *
 * Displays equipped items (weapon, armor, shield).
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { Equipment } from '../../types/generated/GameState.js';

export interface EquipmentSlotsProps {
  equipment: Equipment;
}

/**
 * Equipment slots component
 */
export class EquipmentSlots extends Component<EquipmentSlotsProps> {
  constructor(props: EquipmentSlotsProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'equipment-slots' });

    const header = div({ class: 'equipment-slots__header' }, 'Equipment');
    container.appendChild(header);

    const slots = [
      { key: 'weapon' as const, label: '⚔️ Weapon', value: this.props.equipment.weapon },
      { key: 'armor' as const, label: '🛡️ Armor', value: this.props.equipment.armor },
      { key: 'shield' as const, label: '🛡️ Shield', value: this.props.equipment.shield },
    ];

    const slotsList = div({ class: 'equipment-slots-list' });

    for (const slot of slots) {
      const slotRow = div({ class: 'equipment-slot' });

      const label = div({ class: 'equipment-slot__label' }, slot.label);
      const value = div(
        { class: `equipment-slot__value ${slot.value ? '' : 'equipment-slot__value--empty'}` },
        slot.value || 'None'
      );

      slotRow.appendChild(label);
      slotRow.appendChild(value);

      slotsList.appendChild(slotRow);
    }

    container.appendChild(slotsList);

    return container;
  }
}
