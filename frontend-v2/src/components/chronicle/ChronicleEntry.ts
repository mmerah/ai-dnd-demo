/**
 * ChronicleEntry Component
 *
 * Displays a single journal entry card with edit and delete functionality.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';

export interface ChronicleEntryProps {
  entry: PlayerJournalEntry;
  onEdit: (entryId: string) => void;
  onDelete: (entryId: string) => void;
  onTogglePin: (entryId: string) => void;
}

/**
 * Chronicle entry card component
 */
export class ChronicleEntry extends Component<ChronicleEntryProps> {
  constructor(props: ChronicleEntryProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { entry } = this.props;

    const card = div({
      class: entry.pinned ? 'chronicle-entry chronicle-entry--pinned' : 'chronicle-entry'
    });

    // Pin indicator
    if (entry.pinned) {
      const pinIndicator = div({ class: 'chronicle-entry__pin-indicator' }, '📌');
      card.appendChild(pinIndicator);
    }

    // Content preview (truncated)
    const content = div({ class: 'chronicle-entry__content' });
    content.textContent = this.truncateContent(entry.content);

    // Tags section
    if (entry.tags && entry.tags.length > 0) {
      const tagsContainer = div({ class: 'chronicle-entry__tags' });
      entry.tags.forEach((tag) => {
        const tagBadge = div({ class: 'chronicle-entry__tag' }, tag);
        tagsContainer.appendChild(tagBadge);
      });
      card.appendChild(tagsContainer);
    }

    // Metadata section
    const metadata = div({ class: 'chronicle-entry__metadata' });

    // Timestamp
    const timestamp = div(
      { class: 'chronicle-entry__timestamp' },
      this.formatTimestamp(entry.created_at || '')
    );
    metadata.appendChild(timestamp);

    // Actions section
    const actions = div({ class: 'chronicle-entry__actions' });

    const pinButton = button(entry.pinned ? 'Unpin' : 'Pin', {
      class: 'chronicle-entry__button chronicle-entry__button--pin',
      onclick: () => this.handleTogglePin(),
    });

    const editButton = button('Edit', {
      class: 'chronicle-entry__button chronicle-entry__button--edit',
      onclick: () => this.handleEdit(),
    });

    const deleteButton = button('Delete', {
      class: 'chronicle-entry__button chronicle-entry__button--delete',
      onclick: () => this.handleDelete(),
    });

    actions.appendChild(pinButton);
    actions.appendChild(editButton);
    actions.appendChild(deleteButton);

    // Assemble card
    card.appendChild(content);
    card.appendChild(metadata);
    card.appendChild(actions);

    return card;
  }

  private handleTogglePin(): void {
    this.props.onTogglePin(this.props.entry.entry_id);
  }

  private handleEdit(): void {
    this.props.onEdit(this.props.entry.entry_id);
  }

  private handleDelete(): void {
    const preview = this.truncateContent(this.props.entry.content, 50);
    const confirmed = confirm(
      `Are you sure you want to delete this entry?\n\n"${preview}"`
    );

    if (confirmed) {
      this.props.onDelete(this.props.entry.entry_id);
    }
  }

  private truncateContent(content: string, maxLength: number = 150): string {
    if (content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength).trim() + '...';
  }

  private formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  }
}
