/**
 * CatalogSidebar Component
 *
 * Displays category list and content pack filter.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import { ContentPackFilter } from './ContentPackFilter.js';
import type { ContentPackSummary } from '../../types/generated/ContentPackSummary.js';

export type CatalogCategory = 'spells' | 'items' | 'monsters' | 'races' | 'classes' | 'backgrounds' | 'feats';

export interface CatalogSidebarProps {
  categories: Array<{ id: CatalogCategory; label: string }>;
  selectedCategory: CatalogCategory;
  onCategoryChange: (category: CatalogCategory) => void;
  contentPacks: ContentPackSummary[];
  selectedPacks: string[];
  onPacksChange: (packs: string[]) => void;
}

/**
 * Catalog sidebar component
 */
export class CatalogSidebar extends Component<CatalogSidebarProps> {
  private contentPackFilter: ContentPackFilter | null = null;

  constructor(props: CatalogSidebarProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'catalog-sidebar' });

    // Categories section
    const categoriesSection = div({ class: 'catalog-sidebar__section' });
    const categoriesHeader = div({ class: 'catalog-sidebar__header' }, 'Categories');
    categoriesSection.appendChild(categoriesHeader);

    const categoriesList = div({ class: 'catalog-sidebar__categories' });
    for (const category of this.props.categories) {
      const categoryItem = div({
        class: `catalog-sidebar__category ${category.id === this.props.selectedCategory ? 'catalog-sidebar__category--active' : ''}`,
        onclick: () => this.handleCategoryClick(category.id),
      }, category.label);
      categoriesList.appendChild(categoryItem);
    }
    categoriesSection.appendChild(categoriesList);
    container.appendChild(categoriesSection);

    // Content pack filter section
    const filterSection = div({ class: 'catalog-sidebar__section' });
    this.contentPackFilter = new ContentPackFilter({
      contentPacks: this.props.contentPacks,
      selectedPacks: this.props.selectedPacks,
      onSelectionChange: (packs) => this.props.onPacksChange(packs),
    });
    this.contentPackFilter.mount(filterSection);
    container.appendChild(filterSection);

    return container;
  }

  private handleCategoryClick(category: CatalogCategory): void {
    this.props.onCategoryChange(category);
  }

  override onUnmount(): void {
    if (this.contentPackFilter) {
      this.contentPackFilter.unmount();
      this.contentPackFilter = null;
    }
  }
}
