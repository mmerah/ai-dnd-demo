/**
 * ContentPackFilter Component
 *
 * Displays checkboxes for filtering catalog items by content pack.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { ContentPackSummary } from '../../types/generated/ContentPackSummary.js';

export interface ContentPackFilterProps {
  contentPacks: ContentPackSummary[];
  selectedPacks: string[];
  onSelectionChange: (selectedPacks: string[]) => void;
}

/**
 * Content pack filter component
 */
export class ContentPackFilter extends Component<ContentPackFilterProps> {
  constructor(props: ContentPackFilterProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'content-pack-filter' });

    const header = div({ class: 'content-pack-filter__header' }, 'Content Packs');
    container.appendChild(header);

    const filterList = div({ class: 'content-pack-filter__list' });

    // "All Content Packs" option
    const allOption = this.renderFilterOption('all', 'All Content Packs');
    filterList.appendChild(allOption);

    // Individual content pack options
    for (const pack of this.props.contentPacks) {
      const option = this.renderFilterOption(pack.id, pack.name);
      filterList.appendChild(option);
    }

    container.appendChild(filterList);

    return container;
  }

  private renderFilterOption(packId: string, packName: string): HTMLElement {
    const option = div({ class: 'content-pack-filter__option' });

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `pack-${packId}`;
    checkbox.className = 'content-pack-filter__checkbox';
    checkbox.checked = this.props.selectedPacks.includes(packId);

    checkbox.addEventListener('change', () => {
      this.handlePackToggle(packId, checkbox.checked);
    });

    const label = document.createElement('label');
    label.htmlFor = `pack-${packId}`;
    label.className = 'content-pack-filter__label';
    label.textContent = packName;

    option.appendChild(checkbox);
    option.appendChild(label);

    return option;
  }

  private handlePackToggle(packId: string, isChecked: boolean): void {
    let newSelection: string[];

    if (packId === 'all') {
      // If "All" is checked, select all packs
      if (isChecked) {
        newSelection = ['all', ...this.props.contentPacks.map(p => p.id)];
      } else {
        newSelection = [];
      }
    } else {
      // Toggle individual pack
      if (isChecked) {
        newSelection = [...this.props.selectedPacks, packId];
        // Remove "all" if it was selected
        newSelection = newSelection.filter(id => id !== 'all');
      } else {
        newSelection = this.props.selectedPacks.filter(id => id !== packId);
        // Also remove "all"
        newSelection = newSelection.filter(id => id !== 'all');
      }
    }

    this.props.onSelectionChange(newSelection);
  }
}
