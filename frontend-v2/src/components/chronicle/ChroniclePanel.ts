/**
 * ChroniclePanel Component
 *
 * Enhanced chronicle/journal panel with:
 * - Tabs: All / World / Locations / NPCs / My Notes
 * - Search functionality (content, tags, NPC names)
 * - Location filter toggle
 * - Collapsible header
 * - Auto-generated memory entries (world/location/NPC)
 * - Player journal entries (CRUD)
 */

import { Component } from '../base/Component.js';
import { div, button, createElement } from '../../utils/dom.js';
import { ChronicleEntry } from './ChronicleEntry.js';
import { JournalEntryModal, type EntryFormData } from './JournalEntryModal.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';
import type { JournalApiService } from '../../services/api/JournalApiService.js';
import type { GameState } from '../../types/generated/GameState.js';
import type { StateStore } from '../../services/state/StateStore.js';
import type { MemoryEntry } from '../../types/generated/MemoryEntry.js';

export interface ChroniclePanelProps {
  gameId: string;
  journalApiService: JournalApiService;
  stateStore: StateStore;
  onReloadGameState: () => Promise<void>;
}

type ChronicleFilterType = 'all' | 'world' | 'locations' | 'npcs' | 'notes';

interface AggregatedEntry {
  type: 'world' | 'location' | 'npc' | 'player';
  badge: string;
  timestamp: Date;
  content: string;
  tags: string[];
  locationId?: string;
  npcIds?: string[];
  npcName?: string;
  entryId?: string;
  editable: boolean;
  pinned: boolean;
}

/**
 * Chronicle panel component with tabs, search, filtering, and collapsible header
 */
export class ChroniclePanel extends Component<ChroniclePanelProps> {
  private entries: AggregatedEntry[] = [];
  private entryComponents: ChronicleEntry[] = [];
  private entriesContainer: HTMLElement | null = null;
  private searchInput: HTMLInputElement | null = null;
  private searchClearButton: HTMLButtonElement | null = null;
  private showAllLocationsCheckbox: HTMLInputElement | null = null;
  private modal: JournalEntryModal | null = null;
  private editingEntryId: string | null = null;
  private isCollapsed: boolean = false;

  // Filter state
  private currentFilter: ChronicleFilterType = 'all';
  private searchQuery: string = '';
  private showAllLocations: boolean = false;

  constructor(props: ChroniclePanelProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const panel = div({ class: 'chronicle-panel' });

    // Collapsible header
    const header = div({ class: 'chronicle-panel__header collapsible-header' });
    header.addEventListener('click', () => this.toggleCollapse());

    const headerTop = div({ class: 'chronicle-panel__header-top' });
    const title = div({ class: 'chronicle-panel__title' }, 'Chronicle');
    const collapseIcon = div({ class: 'chronicle-panel__collapse-icon' }, '▼');
    headerTop.appendChild(title);
    headerTop.appendChild(collapseIcon);

    header.appendChild(headerTop);

    // Content area (hidden when collapsed)
    const content = div({ class: 'chronicle-panel__content' });

    // Tabs
    const tabsContainer = div({ class: 'chronicle-panel__tabs' });

    const tabs: Array<{ filter: ChronicleFilterType; label: string }> = [
      { filter: 'all', label: 'All' },
      { filter: 'world', label: 'World' },
      { filter: 'locations', label: 'Locations' },
      { filter: 'npcs', label: 'NPCs' },
      { filter: 'notes', label: 'My Notes' },
    ];

    tabs.forEach(({ filter, label }) => {
      const tabButton = button(label, {
        class: `chronicle-tab ${filter === this.currentFilter ? 'active' : ''}`,
        'data-filter': filter,
        onclick: () => this.handleTabClick(filter),
      });
      tabsContainer.appendChild(tabButton);
    });

    // Search box
    const searchContainer = div({ class: 'chronicle-panel__search' });
    this.searchInput = createElement('input', {
      type: 'text',
      class: 'chronicle-panel__search-input',
      placeholder: 'Search entries...',
    }) as HTMLInputElement;
    this.searchInput.addEventListener('input', () => this.handleSearchInput());

    this.searchClearButton = button('✕', {
      class: 'chronicle-panel__search-clear',
      style: 'display: none;',
      onclick: () => this.handleSearchClear(),
    }) as HTMLButtonElement;

    searchContainer.appendChild(this.searchInput);
    searchContainer.appendChild(this.searchClearButton);

    // Location filter toggle
    const filterContainer = div({ class: 'chronicle-panel__filter' });
    const filterLabel = createElement('label', { class: 'chronicle-panel__filter-label' });
    this.showAllLocationsCheckbox = createElement('input', {
      type: 'checkbox',
      class: 'chronicle-panel__filter-checkbox',
    }) as HTMLInputElement;
    this.showAllLocationsCheckbox.addEventListener('change', () => this.handleLocationFilterChange());
    filterLabel.appendChild(this.showAllLocationsCheckbox);
    filterLabel.appendChild(document.createTextNode(' Show all locations'));
    filterContainer.appendChild(filterLabel);

    // Add entry button
    const addButton = button('+ Add Entry', {
      class: 'chronicle-panel__add-btn',
      onclick: () => this.handleAddEntry(),
    });

    // Entries container
    this.entriesContainer = div({ class: 'chronicle-panel__entries' });

    // Assemble content
    content.appendChild(tabsContainer);
    content.appendChild(searchContainer);
    content.appendChild(filterContainer);
    content.appendChild(addButton);
    content.appendChild(this.entriesContainer);

    // Assemble panel
    panel.appendChild(header);
    panel.appendChild(content);

    return panel;
  }

  override onMount(): void {
    // Subscribe to game state changes to aggregate memories
    this.subscribeImmediate(
      this.props.stateStore.gameState$,
      (gameState) => {
        if (gameState) {
          this.aggregateEntries(gameState);
        } else {
          this.entries = [];
          this.renderEntries();
        }
      }
    );
  }

  override onUnmount(): void {
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];

    if (this.modal) {
      this.modal.unmount();
      this.modal = null;
    }
  }

  private toggleCollapse(): void {
    this.isCollapsed = !this.isCollapsed;
    const panel = this.getElement();
    const content = panel?.querySelector('.chronicle-panel__content');

    if (this.isCollapsed) {
      panel?.classList.add('collapsed');
      content?.classList.add('collapsed');
    } else {
      panel?.classList.remove('collapsed');
      content?.classList.remove('collapsed');
    }
  }

  private handleTabClick(filter: ChronicleFilterType): void {
    this.currentFilter = filter;

    // Update active tab
    const tabs = this.getElement()?.querySelectorAll('.chronicle-tab');
    tabs?.forEach((tab) => {
      const tabElement = tab as HTMLElement;
      if (tabElement.dataset['filter'] === filter) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });

    this.renderEntries();
  }

  private handleSearchInput(): void {
    if (!this.searchInput || !this.searchClearButton) return;

    this.searchQuery = this.searchInput.value.trim().toLowerCase();
    this.searchClearButton.style.display = this.searchQuery ? 'block' : 'none';
    this.renderEntries();
  }

  private handleSearchClear(): void {
    if (!this.searchInput || !this.searchClearButton) return;

    this.searchQuery = '';
    this.searchInput.value = '';
    this.searchClearButton.style.display = 'none';
    this.renderEntries();
  }

  private handleLocationFilterChange(): void {
    if (!this.showAllLocationsCheckbox) return;

    this.showAllLocations = this.showAllLocationsCheckbox.checked;

    // Re-aggregate entries with new filter
    const gameState = this.props.stateStore.getGameState();
    if (gameState) {
      this.aggregateEntries(gameState);
    }
  }

  /**
   * Aggregate all chronicle entries from game state:
   * 1. World memories
   * 2. Location memories (filtered by current location unless "show all" is enabled)
   * 3. NPC memories (filtered by current location unless "show all" is enabled)
   * 4. Player journal entries
   */
  private aggregateEntries(gameState: GameState): void {
    const entries: AggregatedEntry[] = [];
    const currentLocationId = gameState.scenario_instance?.current_location_id;

    // 1. World Memories
    if (gameState.scenario_instance?.world_memories) {
      gameState.scenario_instance.world_memories.forEach((memory: MemoryEntry) => {
        entries.push({
          type: 'world',
          badge: 'WORLD',
          timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
          content: memory.summary,
          tags: memory.tags || [],
          locationId: memory.location_id ?? undefined,
          npcIds: memory.npc_ids || [],
          editable: false,
          pinned: false,
        });
      });
    }

    // 2. Location Memories
    if (gameState.scenario_instance?.location_states) {
      Object.entries(gameState.scenario_instance.location_states).forEach(([locId, locState]) => {
        // Filter by current location unless "show all" is enabled
        if (!this.showAllLocations && locId !== currentLocationId && this.currentFilter !== 'all') {
          return;
        }

        if (locState.location_memories) {
          locState.location_memories.forEach((memory: MemoryEntry) => {
            entries.push({
              type: 'location',
              badge: 'LOCATION',
              timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
              content: memory.summary,
              tags: memory.tags || [],
              locationId: (memory.location_id ?? locId) || undefined,
              npcIds: memory.npc_ids || [],
              editable: false,
              pinned: false,
            });
          });
        }
      });
    }

    // 3. NPC Memories
    if (gameState.npcs) {
      gameState.npcs.forEach((npc) => {
        // Filter by current location unless "show all" is enabled
        if (!this.showAllLocations && npc.current_location_id !== currentLocationId && this.currentFilter !== 'all') {
          return;
        }

        if (npc.npc_memories) {
          npc.npc_memories.forEach((memory: MemoryEntry) => {
            entries.push({
              type: 'npc',
              badge: 'NPC',
              timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
              content: memory.summary,
              tags: memory.tags || [],
              locationId: memory.location_id ?? undefined,
              npcIds: memory.npc_ids || [],
              npcName: npc.sheet?.character?.name || 'Unknown NPC',
              editable: false,
              pinned: false,
            });
          });
        }
      });
    }

    // 4. Player Journal Entries
    if (gameState.player_journal_entries) {
      gameState.player_journal_entries.forEach((entry) => {
        entries.push({
          type: 'player',
          badge: 'PLAYER',
          timestamp: entry.created_at ? new Date(entry.created_at) : new Date(),
          content: entry.content,
          tags: entry.tags || [],
          locationId: entry.location_id ?? undefined,
          npcIds: entry.npc_ids || [],
          entryId: entry.entry_id,
          editable: true,
          pinned: entry.pinned || false,
        });
      });
    }

    this.entries = entries;
    this.renderEntries();
  }

  private renderEntries(): void {
    if (!this.entriesContainer) return;

    // Clear existing entries
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];
    this.entriesContainer.innerHTML = '';

    // Filter entries
    const filteredEntries = this.filterEntries(this.entries);

    if (filteredEntries.length === 0) {
      const empty = div(
        { class: 'chronicle-panel__empty' },
        this.searchQuery
          ? 'No entries match your search.'
          : 'No chronicle entries yet. Start your adventure!'
      );
      this.entriesContainer.appendChild(empty);
      return;
    }

    // Sort entries: pinned first, then by newest
    const sortedEntries = [...filteredEntries].sort((a, b) => {
      // Pinned entries first
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;

      // Then by creation date (newest first)
      return b.timestamp.getTime() - a.timestamp.getTime();
    });

    sortedEntries.forEach((entry) => {
      const gameState = this.props.stateStore.getGameState();

      const entryComponent = new ChronicleEntry({
        entry: this.convertToDisplayEntry(entry),
        gameTime: gameState?.game_time,
        scenarioLocations: gameState?.scenario_instance?.sheet?.locations,
        onEdit: entry.editable && entry.entryId ? (entryId) => this.handleEditEntry(entryId) : undefined,
        onDelete: entry.editable && entry.entryId ? (entryId) => this.handleDeleteEntry(entryId) : undefined,
        onTogglePin: entry.editable && entry.entryId ? (entryId) => this.handleTogglePin(entryId) : undefined,
      });

      entryComponent.mount(this.entriesContainer!);
      this.entryComponents.push(entryComponent);
    });
  }

  /**
   * Convert aggregated entry to display format for ChronicleEntry component
   */
  private convertToDisplayEntry(entry: AggregatedEntry): PlayerJournalEntry {
    return {
      entry_id: entry.entryId || `${entry.type}-${entry.timestamp.getTime()}`,
      content: entry.content,
      tags: entry.tags,
      created_at: entry.timestamp.toISOString(),
      updated_at: entry.timestamp.toISOString(),
      pinned: entry.pinned,
      location_id: entry.locationId,
      npc_ids: entry.npcIds || [],
    };
  }

  /**
   * Filter entries by active tab and search query
   */
  private filterEntries(entries: AggregatedEntry[]): AggregatedEntry[] {
    let filtered = [...entries];

    // Filter by tab
    if (this.currentFilter !== 'all') {
      filtered = filtered.filter((entry) => {
        switch (this.currentFilter) {
          case 'world':
            return entry.type === 'world';
          case 'locations':
            return entry.type === 'location';
          case 'npcs':
            return entry.type === 'npc';
          case 'notes':
            return entry.type === 'player';
          default:
            return true;
        }
      });
    }

    // Filter by search query (searches content, tags, and NPC names)
    if (this.searchQuery) {
      filtered = filtered.filter((entry) => {
        const contentMatch = entry.content.toLowerCase().includes(this.searchQuery);
        const tagMatch = entry.tags.some((tag) => tag.toLowerCase().includes(this.searchQuery));
        const npcMatch = entry.npcName ? entry.npcName.toLowerCase().includes(this.searchQuery) : false;

        return contentMatch || tagMatch || npcMatch;
      });
    }

    return filtered;
  }

  private handleAddEntry(): void {
    this.editingEntryId = null;
    this.showModal({
      onSave: (data: EntryFormData) => this.handleSaveEntry(data),
      onCancel: () => this.hideModal(),
    });
  }

  private handleEditEntry(entryId: string): void {
    // Find the player journal entry
    const gameState = this.props.stateStore.getGameState();
    const entry = gameState?.player_journal_entries?.find((e) => e.entry_id === entryId);
    if (!entry) return;

    this.editingEntryId = entryId;
    this.showModal({
      entry,
      onSave: (data: EntryFormData) => this.handleSaveEntry(data),
      onCancel: () => this.hideModal(),
    });
  }

  private async handleDeleteEntry(entryId: string): Promise<void> {
    try {
      await this.props.journalApiService.deleteEntry(this.props.gameId, entryId);
      await this.props.onReloadGameState();
    } catch (error) {
      console.error('Failed to delete entry:', error);
      alert('Failed to delete entry');
    }
  }

  private async handleTogglePin(entryId: string): Promise<void> {
    try {
      await this.props.journalApiService.togglePin(this.props.gameId, entryId);
      await this.props.onReloadGameState();
    } catch (error) {
      console.error('Failed to toggle pin:', error);
      alert('Failed to toggle pin status');
    }
  }

  private async handleSaveEntry(data: EntryFormData): Promise<void> {
    try {
      if (this.editingEntryId) {
        // Update existing entry
        await this.props.journalApiService.updateEntry(
          this.props.gameId,
          this.editingEntryId,
          { content: data.content, tags: data.tags || [] }
        );
      } else {
        // Create new entry
        await this.props.journalApiService.createEntry(
          this.props.gameId,
          { content: data.content, tags: data.tags || [] }
        );
      }

      await this.props.onReloadGameState();
      this.hideModal();
    } catch (error) {
      console.error('Failed to save entry:', error);
      alert('Failed to save entry');
    }
  }

  private showModal(props: { entry?: PlayerJournalEntry; onSave: (data: EntryFormData) => void; onCancel: () => void }): void {
    if (this.modal) {
      this.modal.unmount();
    }

    this.modal = new JournalEntryModal(props);
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
