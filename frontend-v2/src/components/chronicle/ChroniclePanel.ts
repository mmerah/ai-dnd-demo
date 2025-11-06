/**
 * ChroniclePanel Component
 *
 * Main chronicle/journal panel with CRUD functionality.
 * Uses backend PlayerJournalEntry structure (content + tags only).
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import { ChronicleEntry } from './ChronicleEntry.js';
import { JournalEntryModal, type EntryFormData } from './JournalEntryModal.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';
import type { JournalApiService } from '../../services/api/JournalApiService.js';

export interface ChroniclePanelProps {
  gameId: string;
  journalApiService: JournalApiService;
  onReloadGameState: () => Promise<void>;
}

/**
 * Chronicle panel component with full CRUD
 */
export class ChroniclePanel extends Component<ChroniclePanelProps> {
  private entries: PlayerJournalEntry[] = [];
  private entryComponents: ChronicleEntry[] = [];
  private entriesContainer: HTMLElement | null = null;
  private modal: JournalEntryModal | null = null;
  private editingEntryId: string | null = null;
  private isLoading: boolean = false;

  constructor(props: ChroniclePanelProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const panel = div({ class: 'chronicle-panel' });

    // Header
    const header = div({ class: 'chronicle-panel__header' });
    const title = div({ class: 'chronicle-panel__title' }, 'Chronicle');

    const addButton = button('+ Add Entry', {
      class: 'chronicle-panel__add-btn',
      onclick: () => this.handleAddEntry(),
    });

    header.appendChild(title);
    header.appendChild(addButton);

    // Entries container
    this.entriesContainer = div({ class: 'chronicle-panel__entries' });

    // Assemble panel
    panel.appendChild(header);
    panel.appendChild(this.entriesContainer);

    return panel;
  }

  override onMount(): void {
    this.loadEntries();
  }

  override onUnmount(): void {
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];

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
      this.entries = await this.props.journalApiService.getEntries(this.props.gameId);
      this.renderEntries();
    } catch (error) {
      console.error('Failed to load chronicle entries:', error);
      this.showError('Failed to load chronicle entries');
    } finally {
      this.isLoading = false;
    }
  }

  private renderEntries(): void {
    if (!this.entriesContainer) return;

    // Clear existing entries
    this.entryComponents.forEach((comp) => comp.unmount());
    this.entryComponents = [];
    this.entriesContainer.innerHTML = '';

    if (this.entries.length === 0) {
      const empty = div(
        { class: 'chronicle-panel__empty' },
        'No chronicle entries yet. Click "+ Add Entry" to create one.'
      );
      this.entriesContainer.appendChild(empty);
      return;
    }

    // Sort entries: pinned first, then by newest
    const sortedEntries = [...this.entries].sort((a, b) => {
      // Pinned entries first
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;

      // Then by creation date (newest first)
      const timeA = new Date(a.created_at || '').getTime();
      const timeB = new Date(b.created_at || '').getTime();
      return timeB - timeA;
    });

    sortedEntries.forEach((entry) => {
      const entryComponent = new ChronicleEntry({
        entry,
        onEdit: (entryId) => this.handleEditEntry(entryId),
        onDelete: (entryId) => this.handleDeleteEntry(entryId),
        onTogglePin: (entryId) => this.handleTogglePin(entryId),
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

  private handleAddEntry(): void {
    this.editingEntryId = null;
    this.showModal({
      onSave: (data: EntryFormData) => this.handleSaveEntry(data),
      onCancel: () => this.hideModal(),
    });
  }

  private handleEditEntry(entryId: string): void {
    const entry = this.entries.find((e) => e.entry_id === entryId);
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
      await this.loadEntries();
    } catch (error) {
      console.error('Failed to delete entry:', error);
      alert('Failed to delete entry');
    }
  }

  private async handleTogglePin(entryId: string): Promise<void> {
    try {
      await this.props.journalApiService.togglePin(this.props.gameId, entryId);
      await this.props.onReloadGameState();
      await this.loadEntries();
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
      await this.loadEntries();
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
