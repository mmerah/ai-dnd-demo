/**
 * ChronicleEntry Component
 *
 * Displays a single journal entry card with edit and delete functionality.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { JournalEntry } from '../../services/api/JournalApiService.js';

export interface ChronicleEntryProps {
  entry: JournalEntry;
  onEdit: (entryId: string) => void;
  onDelete: (entryId: string) => void;
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

    const card = div({ class: 'chronicle-entry' });

    // Category badge
    const categoryBadge = div(
      {
        class: `chronicle-entry__category chronicle-entry__category--${entry.category.toLowerCase()}`,
      },
      entry.category
    );

    // Title
    const title = div({ class: 'chronicle-entry__title' }, entry.title);

    // Content preview (truncated)
    const content = div({ class: 'chronicle-entry__content' });
    content.textContent = this.truncateContent(entry.content);

    // Metadata section
    const metadata = div({ class: 'chronicle-entry__metadata' });

    // Location badge (if present)
    if (entry.location) {
      const locationBadge = div(
        { class: 'chronicle-entry__location' },
        `📍 ${entry.location}`
      );
      metadata.appendChild(locationBadge);
    }

    // Timestamp
    const timestamp = div(
      { class: 'chronicle-entry__timestamp' },
      this.formatTimestamp(entry.timestamp || entry.created_at)
    );
    metadata.appendChild(timestamp);

    // Actions section
    const actions = div({ class: 'chronicle-entry__actions' });

    const editButton = button('Edit', {
      class: 'chronicle-entry__button chronicle-entry__button--edit',
      onclick: () => this.handleEdit(),
    });

    const deleteButton = button('Delete', {
      class: 'chronicle-entry__button chronicle-entry__button--delete',
      onclick: () => this.handleDelete(),
    });

    actions.appendChild(editButton);
    actions.appendChild(deleteButton);

    // Assemble card
    card.appendChild(categoryBadge);
    card.appendChild(title);
    card.appendChild(content);
    card.appendChild(metadata);
    card.appendChild(actions);

    return card;
  }

  private handleEdit(): void {
    this.props.onEdit(this.props.entry.id);
  }

  private handleDelete(): void {
    const confirmed = confirm(
      `Are you sure you want to delete this entry?\n\n"${this.props.entry.title}"`
    );

    if (confirmed) {
      this.props.onDelete(this.props.entry.id);
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
