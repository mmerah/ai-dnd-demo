/**
 * ItemList Component
 *
 * Displays the character's inventory items.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { InventoryItem } from '../../types/generated/GameState.js';

export interface ItemListProps {
  items: InventoryItem[];
}

/**
 * Item list component
 */
export class ItemList extends Component<ItemListProps> {
  constructor(props: ItemListProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'item-list' });

    const header = div({ class: 'item-list__header' }, 'Inventory Items');
    container.appendChild(header);

    if (this.props.items.length === 0) {
      const empty = div({ class: 'item-list__empty' }, 'No items in inventory');
      container.appendChild(empty);
      return container;
    }

    // Calculate total weight
    const totalWeight = this.props.items.reduce(
      (sum, item) => sum + ((item.quantity ?? 1) * 0.1), // Assume 0.1 lbs per item if no weight
      0
    );

    const weightDisplay = div(
      { class: 'item-list__weight' },
      `Total Weight: ${totalWeight.toFixed(1)} lbs`
    );
    container.appendChild(weightDisplay);

    // Items list
    const itemsContainer = div({ class: 'item-list__items' });

    for (const item of this.props.items) {
      const itemRow = div({ class: 'item-row' });

      // Item name and quantity
      const nameContainer = div({ class: 'item-row__name-container' });
      const name = div({ class: 'item-row__name' }, item.name ?? item.index);
      const quantity = div({ class: 'item-row__quantity' }, `×${item.quantity ?? 1}`);
      nameContainer.appendChild(name);
      nameContainer.appendChild(quantity);

      // Item weight (using simple weight calculation)
      const itemWeight = (item.quantity ?? 1) * 0.1;
      const weight = div(
        { class: 'item-row__weight' },
        `${itemWeight.toFixed(1)} lbs`
      );

      itemRow.appendChild(nameContainer);
      itemRow.appendChild(weight);

      itemsContainer.appendChild(itemRow);
    }

    container.appendChild(itemsContainer);

    return container;
  }
}
