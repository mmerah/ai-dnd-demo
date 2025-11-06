/**
 * EquipmentSlots Component
 *
 * Displays equipped items (weapon, armor, shield).
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { EquipmentSlots as EquipmentSlotsType } from '../../types/generated/GameState.js';

export interface EquipmentSlotsProps {
  equipment: EquipmentSlotsType;
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
      { key: 'main_hand' as const, label: '⚔️ Main Hand', value: this.props.equipment.main_hand },
      { key: 'off_hand' as const, label: '🛡️ Off Hand', value: this.props.equipment.off_hand },
      { key: 'chest' as const, label: '🛡️ Chest', value: this.props.equipment.chest },
      { key: 'head' as const, label: '👑 Head', value: this.props.equipment.head },
      { key: 'hands' as const, label: '🧤 Hands', value: this.props.equipment.hands },
      { key: 'feet' as const, label: '👢 Feet', value: this.props.equipment.feet },
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
