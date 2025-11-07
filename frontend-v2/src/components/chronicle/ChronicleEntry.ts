/**
 * ChronicleEntry Component
 *
 * Displays a single chronicle entry card with type badge and optional edit/delete functionality.
 * Supports both auto-generated memory entries (read-only) and player journal entries (editable).
 */

import { Component } from '../base/Component.js';
import { div, button, span } from '../../utils/dom.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';
import type { GameTime, ScenarioLocation } from '../../types/generated/GameState.js';

export interface ChronicleEntryProps {
  entry: PlayerJournalEntry;
  gameTime?: GameTime;
  scenarioLocations?: ScenarioLocation[];
  onEdit?: (entryId: string) => void;
  onDelete?: (entryId: string) => void;
  onTogglePin?: (entryId: string) => void;
}

/**
 * Chronicle entry card component with type badge and optional actions
 */
export class ChronicleEntry extends Component<ChronicleEntryProps> {
  constructor(props: ChronicleEntryProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { entry } = this.props;

    const card = div({
      class: entry.pinned ? 'chronicle-entry chronicle-entry--pinned' : 'chronicle-entry',
    });

    // Header with badge and timestamp
    const header = div({ class: 'chronicle-entry__header' });

    // Type badge (derived from entry_id prefix for auto-generated entries)
    const entryType = this.getEntryType(entry.entry_id);
    const badge = span({ class: `chronicle-badge chronicle-badge-${entryType}` }, entryType.toUpperCase());
    header.appendChild(badge);

    // Timestamp
    const timestamp = span(
      { class: 'chronicle-entry__timestamp' },
      this.formatTimestamp(entry.created_at || '')
    );
    header.appendChild(timestamp);

    // Pin button (only for editable entries)
    if (this.props.onTogglePin) {
      const pinButton = button(entry.pinned ? '📌' : '📍', {
        class: `chronicle-pin-btn ${entry.pinned ? 'pinned' : ''}`,
        title: entry.pinned ? 'Unpin' : 'Pin',
        onclick: () => this.handleTogglePin(),
      });
      header.appendChild(pinButton);
    }

    // Edit button (only for editable entries)
    if (this.props.onEdit) {
      const editButton = button('Edit', {
        class: 'chronicle-edit-btn',
        onclick: () => this.handleEdit(),
      });
      header.appendChild(editButton);
    }

    card.appendChild(header);

    // Content (preserve newlines by converting to <br> tags)
    const content = div({ class: 'chronicle-entry__content' });
    // Preserve newlines: escape HTML then replace \n with <br>
    let escapedContent = entry.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/\n/g, '<br>');

    // Replace location IDs with human-readable names (matches old frontend behavior)
    escapedContent = this.replaceLocationIds(escapedContent);

    content.innerHTML = escapedContent;
    card.appendChild(content);

    // Tags section
    if (entry.tags && entry.tags.length > 0) {
      const tagsContainer = div({ class: 'chronicle-entry__tags' });
      entry.tags.forEach((tag) => {
        const tagBadge = span({ class: 'chronicle-tag' }, `#${tag}`);
        tagsContainer.appendChild(tagBadge);
      });
      card.appendChild(tagsContainer);
    }

    return card;
  }

  /**
   * Determine entry type from entry_id (auto-generated entries have type- prefix)
   */
  private getEntryType(entryId: string): string {
    if (entryId.startsWith('world-')) return 'world';
    if (entryId.startsWith('location-')) return 'location';
    if (entryId.startsWith('npc-')) return 'npc';
    return 'player';
  }

  /**
   * Replace location IDs with human-readable names (e.g., "location_001" → "Goblin Cave")
   * Matches old frontend behavior
   */
  private replaceLocationIds(content: string): string {
    if (!this.props.scenarioLocations || this.props.scenarioLocations.length === 0) {
      return content;
    }

    let result = content;

    // Replace location IDs that appear in the content
    for (const location of this.props.scenarioLocations) {
      // Create regex to match the location ID (case-insensitive, word boundary)
      const regex = new RegExp(`\\b${location.id}\\b`, 'gi');
      result = result.replace(regex, location.name ?? location.id);
    }

    return result;
  }

  private handleTogglePin(): void {
    if (this.props.onTogglePin) {
      this.props.onTogglePin(this.props.entry.entry_id);
    }
  }

  private handleEdit(): void {
    if (this.props.onEdit) {
      this.props.onEdit(this.props.entry.entry_id);
    }
  }

  /**
   * Format timestamp - use in-game time if available, otherwise relative real time
   */
  private formatTimestamp(timestamp: string): string {
    // Use in-game time if available (matches old frontend behavior)
    if (this.props.gameTime) {
      const day = this.props.gameTime.day ?? 1;
      const hour = this.props.gameTime.hour ?? 12;
      return `Day ${day}, Hour ${hour}`;
    }

    // Fallback to relative real-world time
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      // Show relative time for recent entries
      if (diffDays === 0) {
        if (diffHours === 0) {
          if (diffMins === 0) return 'Just now';
          return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
        }
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      }
      if (diffDays < 7) {
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
      }

      // Show full date for older entries
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  }
}
