import { describe, it, expect } from 'vitest';
import { ChronicleFilterService } from '../ChronicleFilterService';
import type { AggregatedEntry } from '../ChronicleAggregatorService';

describe('ChronicleFilterService', () => {
  const service = new ChronicleFilterService();

  const mockEntries: AggregatedEntry[] = [
    {
      type: 'world',
      badge: 'WORLD',
      timestamp: new Date('2024-01-01T12:00:00Z'),
      content: 'The ancient dragon awakened from its slumber',
      tags: ['dragon', 'awakening'],
      editable: false,
      pinned: false,
    },
    {
      type: 'location',
      badge: 'LOCATION',
      timestamp: new Date('2024-01-02T12:00:00Z'),
      content: 'You discovered a hidden cave',
      tags: ['discovery', 'cave'],
      locationId: 'loc-1',
      editable: false,
      pinned: true,
    },
    {
      type: 'npc',
      badge: 'NPC',
      timestamp: new Date('2024-01-03T12:00:00Z'),
      content: 'Gandalf shared wisdom about the quest',
      tags: ['wisdom', 'quest'],
      npcName: 'Gandalf',
      editable: false,
      pinned: false,
    },
    {
      type: 'player',
      badge: 'PLAYER',
      timestamp: new Date('2024-01-04T12:00:00Z'),
      content: 'Remember to check the old ruins tomorrow',
      tags: ['todo', 'ruins'],
      entryId: 'entry-1',
      editable: true,
      pinned: false,
    },
  ];

  describe('filterByTab', () => {
    it('should return all entries when filter is "all"', () => {
      const filtered = service.filterByTab(mockEntries, 'all');

      expect(filtered).toHaveLength(4);
      expect(filtered).toEqual(mockEntries);
    });

    it('should filter to world entries only', () => {
      const filtered = service.filterByTab(mockEntries, 'world');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].type).toBe('world');
      expect(filtered[0].content).toBe('The ancient dragon awakened from its slumber');
    });

    it('should filter to location entries only', () => {
      const filtered = service.filterByTab(mockEntries, 'locations');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].type).toBe('location');
      expect(filtered[0].content).toBe('You discovered a hidden cave');
    });

    it('should filter to NPC entries only', () => {
      const filtered = service.filterByTab(mockEntries, 'npcs');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].type).toBe('npc');
      expect(filtered[0].npcName).toBe('Gandalf');
    });

    it('should filter to player notes only', () => {
      const filtered = service.filterByTab(mockEntries, 'notes');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].type).toBe('player');
      expect(filtered[0].content).toBe('Remember to check the old ruins tomorrow');
    });

    it('should handle empty array', () => {
      const filtered = service.filterByTab([], 'world');

      expect(filtered).toEqual([]);
    });

    it('should return empty array when no entries match filter', () => {
      const worldOnly: AggregatedEntry[] = [mockEntries[0]];
      const filtered = service.filterByTab(worldOnly, 'npcs');

      expect(filtered).toEqual([]);
    });
  });

  describe('filterBySearch', () => {
    it('should return all entries when search query is empty', () => {
      const filtered = service.filterBySearch(mockEntries, '');

      expect(filtered).toEqual(mockEntries);
    });

    it('should filter by content match (case-insensitive)', () => {
      const filtered = service.filterBySearch(mockEntries, 'dragon');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].content).toBe('The ancient dragon awakened from its slumber');
    });

    it('should filter by content match with different case', () => {
      const filtered = service.filterBySearch(mockEntries, 'DRAGON');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].content).toBe('The ancient dragon awakened from its slumber');
    });

    it('should filter by tag match', () => {
      const filtered = service.filterBySearch(mockEntries, 'quest');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].npcName).toBe('Gandalf');
    });

    it('should filter by NPC name match', () => {
      const filtered = service.filterBySearch(mockEntries, 'gandalf');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].npcName).toBe('Gandalf');
    });

    it('should return multiple matches', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date(),
          content: 'A cave appeared',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'location',
          badge: 'LOCATION',
          timestamp: new Date(),
          content: 'You explored the cave',
          tags: ['cave'],
          editable: false,
          pinned: false,
        },
      ];

      const filtered = service.filterBySearch(entries, 'cave');

      expect(filtered).toHaveLength(2);
    });

    it('should return empty array when no matches found', () => {
      const filtered = service.filterBySearch(mockEntries, 'nonexistent');

      expect(filtered).toEqual([]);
    });

    it('should handle partial matches', () => {
      const filtered = service.filterBySearch(mockEntries, 'wis');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].tags).toContain('wisdom');
    });

    it('should not match entries without NPC name when searching for NPC', () => {
      const filtered = service.filterBySearch([mockEntries[0]], 'gandalf');

      expect(filtered).toEqual([]);
    });
  });

  describe('sortEntries', () => {
    it('should sort pinned entries first', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-03T12:00:00Z'),
          content: 'Not pinned',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T12:00:00Z'),
          content: 'Pinned entry',
          tags: [],
          editable: false,
          pinned: true,
        },
      ];

      const sorted = service.sortEntries(entries);

      expect(sorted[0].content).toBe('Pinned entry');
      expect(sorted[1].content).toBe('Not pinned');
    });

    it('should sort by timestamp descending (most recent first)', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T12:00:00Z'),
          content: 'Oldest',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-03T12:00:00Z'),
          content: 'Newest',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-02T12:00:00Z'),
          content: 'Middle',
          tags: [],
          editable: false,
          pinned: false,
        },
      ];

      const sorted = service.sortEntries(entries);

      expect(sorted[0].content).toBe('Newest');
      expect(sorted[1].content).toBe('Middle');
      expect(sorted[2].content).toBe('Oldest');
    });

    it('should sort pinned by timestamp, then unpinned by timestamp', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-02T12:00:00Z'),
          content: 'Unpinned recent',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T12:00:00Z'),
          content: 'Pinned old',
          tags: [],
          editable: false,
          pinned: true,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-03T12:00:00Z'),
          content: 'Pinned recent',
          tags: [],
          editable: false,
          pinned: true,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T06:00:00Z'),
          content: 'Unpinned old',
          tags: [],
          editable: false,
          pinned: false,
        },
      ];

      const sorted = service.sortEntries(entries);

      expect(sorted[0].content).toBe('Pinned recent');
      expect(sorted[1].content).toBe('Pinned old');
      expect(sorted[2].content).toBe('Unpinned recent');
      expect(sorted[3].content).toBe('Unpinned old');
    });

    it('should not mutate original array', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-02T12:00:00Z'),
          content: 'Second',
          tags: [],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T12:00:00Z'),
          content: 'First',
          tags: [],
          editable: false,
          pinned: false,
        },
      ];

      const original = [...entries];
      const sorted = service.sortEntries(entries);

      expect(entries).toEqual(original);
      expect(sorted).not.toBe(entries);
    });

    it('should handle empty array', () => {
      const sorted = service.sortEntries([]);

      expect(sorted).toEqual([]);
    });

    it('should handle single entry', () => {
      const entries: AggregatedEntry[] = [mockEntries[0]];
      const sorted = service.sortEntries(entries);

      expect(sorted).toEqual(entries);
    });
  });

  describe('filterAndSort', () => {
    it('should apply tab filter, search filter, and sorting', () => {
      const entries: AggregatedEntry[] = [
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-01T12:00:00Z'),
          content: 'Dragon event old',
          tags: ['dragon'],
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-03T12:00:00Z'),
          content: 'Dragon event recent',
          tags: ['dragon'],
          editable: false,
          pinned: true,
        },
        {
          type: 'npc',
          badge: 'NPC',
          timestamp: new Date('2024-01-02T12:00:00Z'),
          content: 'NPC talks about dragon',
          tags: [],
          npcName: 'Wizard',
          editable: false,
          pinned: false,
        },
        {
          type: 'world',
          badge: 'WORLD',
          timestamp: new Date('2024-01-02T12:00:00Z'),
          content: 'Unrelated world event',
          tags: [],
          editable: false,
          pinned: false,
        },
      ];

      const result = service.filterAndSort(entries, 'world', 'dragon');

      expect(result).toHaveLength(2);
      expect(result[0].content).toBe('Dragon event recent'); // Pinned first
      expect(result[1].content).toBe('Dragon event old');
    });

    it('should work with all filters', () => {
      const result = service.filterAndSort(mockEntries, 'all', '');

      expect(result).toHaveLength(4);
      // Sorted by pinned first, then timestamp
      expect(result[0].pinned).toBe(true);
    });

    it('should work with only tab filter', () => {
      const result = service.filterAndSort(mockEntries, 'npcs', '');

      expect(result).toHaveLength(1);
      expect(result[0].type).toBe('npc');
    });

    it('should work with only search filter', () => {
      const result = service.filterAndSort(mockEntries, 'all', 'cave');

      expect(result).toHaveLength(1);
      expect(result[0].content).toBe('You discovered a hidden cave');
    });

    it('should return empty array when filters match nothing', () => {
      const result = service.filterAndSort(mockEntries, 'world', 'nonexistent');

      expect(result).toEqual([]);
    });

    it('should handle empty entries array', () => {
      const result = service.filterAndSort([], 'all', 'test');

      expect(result).toEqual([]);
    });
  });
});
