/**
 * Service responsible for filtering and sorting chronicle entries.
 * Extracted from ChroniclePanel to follow Single Responsibility Principle.
 *
 * Provides filtering by:
 * - Entry type (world/location/npc/player)
 * - Search query (content, tags, NPC names)
 * - Sorting (pinned first, then by date)
 */

import type { AggregatedEntry } from './ChronicleAggregatorService.js';

/**
 * Filter type for chronicle entries
 */
export type ChronicleFilterType = 'all' | 'world' | 'locations' | 'npcs' | 'notes';

/**
 * Service for filtering and sorting chronicle entries
 */
export class ChronicleFilterService {
  /**
   * Filters entries by tab type
   * @param entries - Array of entries to filter
   * @param filterType - Type of entries to show
   * @returns Filtered array of entries
   */
  filterByTab(entries: AggregatedEntry[], filterType: ChronicleFilterType): AggregatedEntry[] {
    if (filterType === 'all') {
      return entries;
    }

    return entries.filter((entry) => {
      switch (filterType) {
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

  /**
   * Filters entries by search query (searches content, tags, and NPC names)
   * @param entries - Array of entries to filter
   * @param searchQuery - Search query string (case-insensitive)
   * @returns Filtered array of entries
   */
  filterBySearch(entries: AggregatedEntry[], searchQuery: string): AggregatedEntry[] {
    if (!searchQuery) {
      return entries;
    }

    const lowerQuery = searchQuery.toLowerCase();

    return entries.filter((entry) => {
      const contentMatch = entry.content.toLowerCase().includes(lowerQuery);
      const tagMatch = entry.tags.some((tag) => tag.toLowerCase().includes(lowerQuery));
      const npcMatch = entry.npcName ? entry.npcName.toLowerCase().includes(lowerQuery) : false;

      return contentMatch || tagMatch || npcMatch;
    });
  }

  /**
   * Sorts entries (pinned first, then by timestamp descending)
   * @param entries - Array of entries to sort
   * @returns Sorted array of entries (does not mutate original)
   */
  sortEntries(entries: AggregatedEntry[]): AggregatedEntry[] {
    return [...entries].sort((a, b) => {
      // Pinned entries come first
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;

      // Sort by timestamp (most recent first)
      return b.timestamp.getTime() - a.timestamp.getTime();
    });
  }

  /**
   * Applies all filters and sorting to entries
   * @param entries - Array of entries to filter and sort
   * @param filterType - Type of entries to show
   * @param searchQuery - Search query string (case-insensitive)
   * @returns Filtered and sorted array of entries
   */
  filterAndSort(
    entries: AggregatedEntry[],
    filterType: ChronicleFilterType,
    searchQuery: string
  ): AggregatedEntry[] {
    let filtered = this.filterByTab(entries, filterType);
    filtered = this.filterBySearch(filtered, searchQuery);
    filtered = this.sortEntries(filtered);

    return filtered;
  }
}
