/**
 * CatalogBrowserScreen
 *
 * Main screen for browsing catalog data (spells, items, monsters, etc.)
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { div, button } from '../utils/dom.js';
import { CatalogSidebar, type CatalogCategory } from '../components/catalog/CatalogSidebar.js';
import { CatalogItemList } from '../components/catalog/CatalogItemList.js';
import { CatalogItemDetail, type CatalogItem } from '../components/catalog/CatalogItemDetail.js';
import { applyAllFilters } from '../utils/catalogFilters.js';
import type { ContentPackSummary } from '../types/generated/ContentPackSummary.js';

export interface CatalogBrowserScreenProps {
  container: ServiceContainer;
  onBack: () => void;
}

const CATEGORIES = [
  { id: 'spells' as const, label: 'Spells' },
  { id: 'items' as const, label: 'Items' },
  { id: 'monsters' as const, label: 'Monsters' },
  { id: 'races' as const, label: 'Races' },
  { id: 'classes' as const, label: 'Classes' },
  { id: 'backgrounds' as const, label: 'Backgrounds' },
  { id: 'feats' as const, label: 'Feats' },
];

export class CatalogBrowserScreen extends Screen {
  private sidebar: CatalogSidebar | null = null;
  private itemList: CatalogItemList<CatalogItem & { index: string }> | null = null;
  private itemDetail: CatalogItemDetail | null = null;

  private selectedCategory: CatalogCategory = 'spells';
  private selectedPacks: string[] = ['all'];
  private searchQuery = '';
  private selectedItem: CatalogItem | null = null;

  private contentPacks: ContentPackSummary[] = [];
  private allItems: CatalogItem[] = [];
  private filteredItems: CatalogItem[] = [];

  constructor(private props: CatalogBrowserScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const screen = div({ class: 'catalog-browser-screen' });

    // Header
    const header = div({ class: 'catalog-browser-screen__header' });
    const title = div({ class: 'catalog-browser-screen__title' }, 'Catalog Browser');
    const backBtn = button('← Back to Game', {
      class: 'catalog-browser-screen__back-button',
      onclick: () => this.props.onBack(),
    });
    header.appendChild(title);
    header.appendChild(backBtn);
    screen.appendChild(header);

    // Main content (sidebar + content area)
    const main = div({ class: 'catalog-browser-screen__main' });

    // Sidebar
    const sidebarContainer = div({ class: 'catalog-browser-screen__sidebar' });
    main.appendChild(sidebarContainer);

    // Content area (item list + detail)
    const contentArea = div({ class: 'catalog-browser-screen__content' });
    const listContainer = div({ class: 'catalog-browser-screen__list' });
    const detailContainer = div({ class: 'catalog-browser-screen__detail' });
    contentArea.appendChild(listContainer);
    contentArea.appendChild(detailContainer);
    main.appendChild(contentArea);

    screen.appendChild(main);

    return screen;
  }

  override onMount(): void {
    this.loadContentPacks();
    this.loadCategory(this.selectedCategory);
    this.renderSidebar();
  }

  private async loadContentPacks(): Promise<void> {
    try {
      const response = await this.props.container.catalogApiService.getContentPacks();
      this.contentPacks = response.packs;
      this.renderSidebar();
    } catch (error) {
      console.error('Failed to load content packs:', error);
    }
  }

  private async loadCategory(category: CatalogCategory): Promise<void> {
    try {
      const { catalogApiService } = this.props.container;

      // Backend returns arrays directly, not wrapped
      switch (category) {
        case 'spells':
          this.allItems = await catalogApiService.getSpells();
          break;
        case 'items':
          this.allItems = await catalogApiService.getItems();
          break;
        case 'monsters':
          this.allItems = await catalogApiService.getMonsters();
          break;
        case 'races':
          this.allItems = await catalogApiService.getRaces();
          break;
        case 'classes':
          this.allItems = await catalogApiService.getClasses();
          break;
        case 'backgrounds':
          this.allItems = await catalogApiService.getBackgrounds();
          break;
        case 'feats':
          this.allItems = await catalogApiService.getFeats();
          break;
      }

      this.applyFilters();
      this.renderItemList();
      this.renderItemDetail();
    } catch (error) {
      console.error(`Failed to load ${category}:`, error);
      this.allItems = [];
      this.applyFilters();
      this.renderItemList();
    }
  }

  private applyFilters(): void {
    this.filteredItems = applyAllFilters(
      this.allItems,
      this.selectedPacks,
      this.searchQuery,
      ['name', 'index', 'content_pack']
    );
  }

  private renderSidebar(): void {
    const container = this.container?.querySelector('.catalog-browser-screen__sidebar');
    if (!container) return;

    if (this.sidebar) {
      this.sidebar.unmount();
    }

    this.sidebar = new CatalogSidebar({
      categories: CATEGORIES,
      selectedCategory: this.selectedCategory,
      onCategoryChange: (category) => this.handleCategoryChange(category),
      contentPacks: this.contentPacks,
      selectedPacks: this.selectedPacks,
      onPacksChange: (packs) => this.handlePacksChange(packs),
    });

    this.registerComponent(this.sidebar);
    this.sidebar.mount(container as HTMLElement);
  }

  private renderItemList(): void {
    const container = this.container?.querySelector('.catalog-browser-screen__list');
    if (!container) return;

    if (this.itemList) {
      this.itemList.unmount();
    }

    this.itemList = new CatalogItemList({
      items: this.filteredItems as Array<CatalogItem & { index: string }>,
      selectedItemId: (this.selectedItem as any)?.index || null,
      onItemSelect: (item) => this.handleItemSelect(item),
      renderItemCard: (item, isSelected) => this.renderItemCard(item, isSelected),
      searchPlaceholder: `Search ${this.selectedCategory}...`,
      onSearchChange: (query) => this.handleSearchChange(query),
    });

    this.registerComponent(this.itemList);
    this.itemList.mount(container as HTMLElement);
  }

  private renderItemDetail(): void {
    const container = this.container?.querySelector('.catalog-browser-screen__detail');
    if (!container) return;

    if (this.itemDetail) {
      this.itemDetail.unmount();
    }

    this.itemDetail = new CatalogItemDetail({
      item: this.selectedItem,
      onClose: () => this.handleItemClose(),
    });

    this.registerComponent(this.itemDetail);
    this.itemDetail.mount(container as HTMLElement);
  }

  private renderItemCard(item: CatalogItem, isSelected: boolean): HTMLElement {
    const card = div({
      class: `catalog-item-card ${isSelected ? 'catalog-item-card--selected' : ''}`,
    });

    const name = div({ class: 'catalog-item-card__name' }, item.name);
    card.appendChild(name);

    // Add category-specific info
    if ('level' in item) {
      const level = div({ class: 'catalog-item-card__meta' }, `Level ${item.level}`);
      card.appendChild(level);
    } else if ('challenge_rating' in item) {
      const cr = div({ class: 'catalog-item-card__meta' }, `CR ${item.challenge_rating}`);
      card.appendChild(cr);
    }

    return card;
  }

  private handleCategoryChange(category: CatalogCategory): void {
    this.selectedCategory = category;
    this.searchQuery = '';
    this.selectedItem = null;

    // Update sidebar to reflect new selected category
    if (this.sidebar) {
      this.sidebar.update({ selectedCategory: category });
    }

    this.loadCategory(category);
  }

  private handlePacksChange(packs: string[]): void {
    this.selectedPacks = packs;
    this.applyFilters();
    this.renderItemList();
  }

  private handleSearchChange(query: string): void {
    this.searchQuery = query;
    this.applyFilters();
    this.renderItemList();
  }

  private handleItemSelect(item: CatalogItem): void {
    this.selectedItem = item;
    this.renderItemList();
    this.renderItemDetail();
  }

  private handleItemClose(): void {
    this.selectedItem = null;
    this.renderItemList();
    this.renderItemDetail();
  }
}
