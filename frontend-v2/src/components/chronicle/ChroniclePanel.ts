/**
 * ChroniclePanel Component
 *
 * Main chronicle/journal panel with CRUD functionality, filtering, and search.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import { ChronicleEntry } from './ChronicleEntry.js';
import { ChronicleFilters, type FilterState } from './ChronicleFilters.js';
import { JournalEntryModal, type EntryFormData, type JournalEntryModalProps } from './JournalEntryModal.js';
import type { JournalEntry as JournalEntryType, JournalApiService } from '../../services/api/JournalApiService.js';

export interface ChroniclePanelProps {
  gameId: string;
  journalApiService: JournalApiService;
  onReloadGameState: () => Promise<void>;
}

/**
 * Chronicle panel component with full CRUD
 */
export class ChroniclePanel extends Component<ChroniclePanelProps> {
  private entries: JournalEntryType[] = [];
  private filteredEntries: JournalEntryType[] = [];
  private entryComponents: ChronicleEntry[] = [];
  private filters: FilterState = {
    category: 'All',
    location: 'All',
    searchQuery: '',
  };

  private entriesContainer: HTMLElement | null = null;
  private filtersPanel: ChronicleFilters | null = null;
  private modal: JournalEntryModal | null = null;
  private editingEntryId: string | null = null;

  private showFilters: boolean = false;
  private isLoading: boolean = false;

  constructor(props: ChroniclePanelProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const panel = div({ class: 'chronicle-panel' });

    // Header
    const header = div({ class: 'chronicle-panel__header' });

    const title = div({ class: 'chronicle-panel__title' }, 'Chronicle');

    const headerActions = div({ class: 'chronicle-panel__header-actions' });

    const toggleFiltersButton = button(this.showFilters ? 'Hide Filters' : 'Show Filters', {
      class: 'chronicle-panel__toggle-filters-btn',
      onclick: () => this.handleToggleFilters(),
    });

    const addButton = button('+ Add Entry', {
      class: 'chronicle-panel__add-btn',
      onclick: () => this.handleAddEntry(),
    });

    headerActions.appendChild(toggleFiltersButton);
    headerActions.appendChild(addButton);

    header.appendChild(title);
    header.appendChild(headerActions);

    // Filters (collapsible)
    const filtersContainer = div({ class: 'chronicle-panel__filters-container' });
    filtersContainer.style.display = this.showFilters ? 'block' : 'none';

    // Entries container
    this.entriesContainer = div({ class: 'chronicle-panel__entries' });

    // Assemble panel
    panel.appendChild(header);
    panel.appendChild(filtersContainer);
    panel.appendChild(this.entriesContainer);

    return panel;
  }

  override onMount(): void {
    this.loadEntries();
  }

  override onUnmount(): void {
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];

    if (this.filtersPanel) {
      this.filtersPanel.unmount();
      this.filtersPanel = null;
    }

    if (this.modal) {
      this.modal.unmount();
      this.modal = null;
    }
  }

  private async loadEntries(): Promise<void> {
    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoading();

    try {
      const response = await this.props.journalApiService.getEntries(this.props.gameId);
      this.entries = response.entries;
      this.applyFilters();
      this.renderEntries();
    } catch (error) {
      console.error('Failed to load chronicle entries:', error);
      this.showError('Failed to load chronicle entries');
    } finally {
      this.isLoading = false;
    }
  }

  private applyFilters(): void {
    let filtered = [...this.entries];

    // Filter by category
    if (this.filters.category !== 'All') {
      filtered = filtered.filter((entry) => entry.category === this.filters.category);
    }

    // Filter by location
    if (this.filters.location !== 'All') {
      filtered = filtered.filter((entry) => entry.location === this.filters.location);
    }

    // Filter by search query
    if (this.filters.searchQuery.trim()) {
      const query = this.filters.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (entry) =>
          entry.title.toLowerCase().includes(query) ||
          entry.content.toLowerCase().includes(query)
      );
    }

    this.filteredEntries = filtered;
  }

  private renderEntries(): void {
    if (!this.entriesContainer) return;

    // Clear existing entries
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];
    this.entriesContainer.innerHTML = '';

    if (this.filteredEntries.length === 0) {
      const empty = div(
        { class: 'chronicle-panel__empty' },
        this.entries.length === 0
          ? 'No chronicle entries yet. Click "+ Add Entry" to create one.'
          : 'No entries match your filters.'
      );
      this.entriesContainer.appendChild(empty);
      return;
    }

    // Render filtered entries (newest first)
    const sortedEntries = [...this.filteredEntries].sort((a, b) => {
      const timeA = new Date(a.timestamp || a.created_at).getTime();
      const timeB = new Date(b.timestamp || b.created_at).getTime();
      return timeB - timeA; // Descending order
    });

    sortedEntries.forEach((entry) => {
      const entryComponent = new ChronicleEntry({
        entry,
        onEdit: (entryId) => this.handleEditEntry(entryId),
        onDelete: (entryId) => this.handleDeleteEntry(entryId),
      });

      entryComponent.mount(this.entriesContainer!);
      this.entryComponents.push(entryComponent);
    });
  }

  private showLoading(): void {
    if (!this.entriesContainer) return;

    this.entriesContainer.innerHTML = '';
    const loading = div({ class: 'chronicle-panel__loading' }, 'Loading entries...');
    this.entriesContainer.appendChild(loading);
  }

  private showError(message: string): void {
    if (!this.entriesContainer) return;

    this.entriesContainer.innerHTML = '';
    const error = div({ class: 'chronicle-panel__error' }, message);
    this.entriesContainer.appendChild(error);
  }

  private handleToggleFilters(): void {
    this.showFilters = !this.showFilters;

    // Re-render to update button text and filters visibility
    if (this.element && this.element.parentElement) {
      // Mount filters if showing
      if (this.showFilters) {
        const filtersContainer = this.element.querySelector('.chronicle-panel__filters-container');
        if (filtersContainer) {
          filtersContainer.innerHTML = '';
          this.mountFilters(filtersContainer as HTMLElement);
          (filtersContainer as HTMLElement).style.display = 'block';
        }
      } else {
        if (this.filtersPanel) {
          this.filtersPanel.unmount();
          this.filtersPanel = null;
        }
        const filtersContainer = this.element.querySelector('.chronicle-panel__filters-container');
        if (filtersContainer) {
          (filtersContainer as HTMLElement).style.display = 'none';
        }
      }

      // Update button text
      const toggleButton = this.element.querySelector('.chronicle-panel__toggle-filters-btn');
      if (toggleButton) {
        toggleButton.textContent = this.showFilters ? 'Hide Filters' : 'Show Filters';
      }
    }
  }

  private mountFilters(container: HTMLElement): void {
    const locations = Array.from(
      new Set(this.entries.map((e) => e.location).filter((l): l is string => !!l))
    );

    this.filtersPanel = new ChronicleFilters({
      onFilterChange: (filters) => this.handleFilterChange(filters),
      locations,
    });

    this.filtersPanel.mount(container);
  }

  private handleFilterChange(filters: FilterState): void {
    this.filters = filters;
    this.applyFilters();
    this.renderEntries();
  }

  private handleAddEntry(): void {
    const locations = Array.from(
      new Set(this.entries.map((e) => e.location).filter((l): l is string => !!l))
    );

    this.editingEntryId = null;
    this.showModal({
      locations,
      onSave: (data: EntryFormData) => this.handleSaveEntry(data),
      onCancel: () => this.hideModal(),
    });
  }

  private handleEditEntry(entryId: string): void {
    const entry = this.entries.find((e) => e.id === entryId);
    if (!entry) return;

    const locations = Array.from(
      new Set(this.entries.map((e) => e.location).filter((l): l is string => !!l))
    );

    this.editingEntryId = entryId;
    this.showModal({
      entry,
      locations,
      onSave: (data: EntryFormData) => this.handleSaveEntry(data),
      onCancel: () => this.hideModal(),
    });
  }

  private async handleDeleteEntry(entryId: string): Promise<void> {
    try {
      await this.props.journalApiService.deleteEntry(this.props.gameId, entryId);
      await this.props.onReloadGameState();
      await this.loadEntries();
    } catch (error) {
      console.error('Failed to delete entry:', error);
      alert('Failed to delete entry');
    }
  }

  private async handleSaveEntry(data: EntryFormData): Promise<void> {
    try {
      if (this.editingEntryId) {
        // Update existing entry
        await this.props.journalApiService.updateEntry(
          this.props.gameId,
          this.editingEntryId,
          data
        );
      } else {
        // Create new entry
        await this.props.journalApiService.createEntry(this.props.gameId, data);
      }

      await this.props.onReloadGameState();
      this.hideModal();
      await this.loadEntries();
    } catch (error) {
      console.error('Failed to save entry:', error);
      alert('Failed to save entry');
    }
  }

  private showModal(props: Omit<JournalEntryModalProps, 'entry'> & { entry?: JournalEntryType }): void {
    if (this.modal) {
      this.modal.unmount();
    }

    this.modal = new JournalEntryModal(props as JournalEntryModalProps);
    this.modal.mount(document.body);
  }

  private hideModal(): void {
    if (this.modal) {
      this.modal.unmount();
      this.modal = null;
    }
    this.editingEntryId = null;
  }
}
