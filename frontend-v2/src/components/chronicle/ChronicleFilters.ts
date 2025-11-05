/**
 * ChronicleFilters Component
 *
 * Filter and search controls for chronicle entries.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';

export interface ChronicleFiltersProps {
  onFilterChange: (filters: FilterState) => void;
  locations: string[];
}

export interface FilterState {
  category: string;
  location: string;
  searchQuery: string;
}

/**
 * Chronicle filters component
 */
export class ChronicleFilters extends Component<ChronicleFiltersProps> {
  private filters: FilterState = {
    category: 'All',
    location: 'All',
    searchQuery: '',
  };

  constructor(props: ChronicleFiltersProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'chronicle-filters' });

    // Category filter
    const categorySection = div({ class: 'chronicle-filters__section' });
    const categoryLabel = div({ class: 'chronicle-filters__label' }, 'Category:');
    const categorySelect = this.createCategorySelect();
    categorySection.appendChild(categoryLabel);
    categorySection.appendChild(categorySelect);

    // Location filter
    const locationSection = div({ class: 'chronicle-filters__section' });
    const locationLabel = div({ class: 'chronicle-filters__label' }, 'Location:');
    const locationSelect = this.createLocationSelect();
    locationSection.appendChild(locationLabel);
    locationSection.appendChild(locationSelect);

    // Search input
    const searchSection = div({ class: 'chronicle-filters__section' });
    const searchLabel = div({ class: 'chronicle-filters__label' }, 'Search:');
    const searchInput = this.createSearchInput();
    searchSection.appendChild(searchLabel);
    searchSection.appendChild(searchInput);

    // Clear button
    const clearButton = button('Clear Filters', {
      class: 'chronicle-filters__clear-btn',
      onclick: () => this.handleClearFilters(),
    });

    container.appendChild(categorySection);
    container.appendChild(locationSection);
    container.appendChild(searchSection);
    container.appendChild(clearButton);

    return container;
  }

  private createCategorySelect(): HTMLElement {
    const select = document.createElement('select');
    select.className = 'chronicle-filters__select';

    const categories = ['All', 'Event', 'NPC', 'Location', 'Quest', 'Item'];
    categories.forEach((category) => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      if (category === this.filters.category) {
        option.selected = true;
      }
      select.appendChild(option);
    });

    select.addEventListener('change', () => {
      this.filters.category = select.value;
      this.notifyFilterChange();
    });

    return select;
  }

  private createLocationSelect(): HTMLElement {
    const select = document.createElement('select');
    select.className = 'chronicle-filters__select';

    const locations = ['All', ...this.props.locations];
    locations.forEach((location) => {
      const option = document.createElement('option');
      option.value = location;
      option.textContent = location;
      if (location === this.filters.location) {
        option.selected = true;
      }
      select.appendChild(option);
    });

    select.addEventListener('change', () => {
      this.filters.location = select.value;
      this.notifyFilterChange();
    });

    return select;
  }

  private createSearchInput(): HTMLElement {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'chronicle-filters__search-input';
    input.placeholder = 'Search entries...';
    input.value = this.filters.searchQuery;

    // Debounced search
    let searchTimeout: ReturnType<typeof setTimeout> | null = null;
    input.addEventListener('input', () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      searchTimeout = setTimeout(() => {
        this.filters.searchQuery = input.value;
        this.notifyFilterChange();
      }, 300);
    });

    return input;
  }

  private handleClearFilters(): void {
    this.filters = {
      category: 'All',
      location: 'All',
      searchQuery: '',
    };
    this.notifyFilterChange();

    // Re-render to reset UI
    if (this.element && this.element.parentElement) {
      const parent = this.element.parentElement;
      this.unmount();
      this.mount(parent);
    }
  }

  private notifyFilterChange(): void {
    this.props.onFilterChange(this.filters);
  }
}
