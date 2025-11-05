/**
 * CatalogItemList Component
 *
 * Displays a list of catalog items with search functionality.
 */

import { Component } from '../base/Component.js';
import { div, input } from '../../utils/dom.js';

export interface CatalogItemListProps<T> {
  items: T[];
  selectedItemId: string | null;
  onItemSelect: (item: T) => void;
  renderItemCard: (item: T, isSelected: boolean) => HTMLElement;
  searchPlaceholder: string;
  onSearchChange: (query: string) => void;
}

/**
 * Catalog item list component
 */
export class CatalogItemList<T extends { id: string }> extends Component<CatalogItemListProps<T>> {
  private searchDebounceTimeout: number | null = null;

  constructor(props: CatalogItemListProps<T>) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'catalog-item-list' });

    // Search input
    const searchContainer = div({ class: 'catalog-item-list__search' });
    const searchInput = input({
      type: 'text',
      class: 'catalog-item-list__search-input',
      placeholder: this.props.searchPlaceholder,
      oninput: (e: Event) => this.handleSearchInput((e.target as HTMLInputElement).value),
    });
    searchContainer.appendChild(searchInput);
    container.appendChild(searchContainer);

    // Item count
    const countDisplay = div(
      { class: 'catalog-item-list__count' },
      `${this.props.items.length} items`
    );
    container.appendChild(countDisplay);

    // Items grid
    const itemsGrid = div({ class: 'catalog-item-list__grid' });

    if (this.props.items.length === 0) {
      const empty = div({ class: 'catalog-item-list__empty' }, 'No items found');
      itemsGrid.appendChild(empty);
    } else {
      for (const item of this.props.items) {
        const isSelected = item.id === this.props.selectedItemId;
        const card = this.props.renderItemCard(item, isSelected);
        card.addEventListener('click', () => this.props.onItemSelect(item));
        itemsGrid.appendChild(card);
      }
    }

    container.appendChild(itemsGrid);

    return container;
  }

  private handleSearchInput(value: string): void {
    // Debounce search input
    if (this.searchDebounceTimeout) {
      clearTimeout(this.searchDebounceTimeout);
    }

    this.searchDebounceTimeout = window.setTimeout(() => {
      this.props.onSearchChange(value);
    }, 300);
  }

  override onUnmount(): void {
    if (this.searchDebounceTimeout) {
      clearTimeout(this.searchDebounceTimeout);
    }
  }
}
