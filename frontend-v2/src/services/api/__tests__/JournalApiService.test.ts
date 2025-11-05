import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  JournalApiService,
  type JournalEntry,
  type CreateJournalEntryRequest,
  type UpdateJournalEntryRequest,
} from '../JournalApiService';
import { ApiService } from '../ApiService';

// Mock ApiService
vi.mock('../ApiService');

describe('JournalApiService', () => {
  let journalApiService: JournalApiService;
  let mockApiService: ApiService;
  const gameId = 'game-123';

  beforeEach(() => {
    mockApiService = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    } as unknown as ApiService;

    journalApiService = new JournalApiService(mockApiService);
  });

  describe('getEntries', () => {
    it('should fetch all journal entries for a game', async () => {
      const mockResponse = {
        entries: [
          {
            id: 'entry-1',
            title: 'Met the Mayor',
            content: 'We met the mayor of Phandalin',
            category: 'NPC' as const,
            location: 'Phandalin',
            timestamp: '2024-01-01T10:00:00Z',
            created_at: '2024-01-01T10:00:00Z',
          },
          {
            id: 'entry-2',
            title: 'Found a sword',
            content: 'Discovered a magic sword in the ruins',
            category: 'Item' as const,
            timestamp: '2024-01-01T12:00:00Z',
            created_at: '2024-01-01T12:00:00Z',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.getEntries(gameId);

      expect(mockApiService.get).toHaveBeenCalledWith(
        '/api/game/game-123/journal'
      );
      expect(result).toEqual(mockResponse);
      expect(result.entries).toHaveLength(2);
    });

    it('should handle empty journal', async () => {
      const mockResponse = { entries: [] };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.getEntries(gameId);

      expect(result.entries).toHaveLength(0);
    });

    it('should propagate fetch errors', async () => {
      const error = new Error('Fetch failed');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(journalApiService.getEntries(gameId)).rejects.toThrow(
        'Fetch failed'
      );
    });
  });

  describe('createEntry', () => {
    it('should create a new journal entry', async () => {
      const newEntry: CreateJournalEntryRequest = {
        title: 'Battle with Goblins',
        content: 'We fought off a goblin ambush',
        category: 'Event',
        location: 'Forest Road',
      };

      const mockResponse: JournalEntry = {
        id: 'entry-3',
        ...newEntry,
        timestamp: '2024-01-01T14:00:00Z',
        created_at: '2024-01-01T14:00:00Z',
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.createEntry(gameId, newEntry);

      expect(mockApiService.post).toHaveBeenCalledWith(
        '/api/game/game-123/journal',
        newEntry
      );
      expect(result).toEqual(mockResponse);
      expect(result.id).toBe('entry-3');
    });

    it('should create entry without optional location', async () => {
      const newEntry: CreateJournalEntryRequest = {
        title: 'General observation',
        content: 'Something interesting happened',
        category: 'Event',
      };

      const mockResponse: JournalEntry = {
        id: 'entry-4',
        ...newEntry,
        timestamp: '2024-01-01T15:00:00Z',
        created_at: '2024-01-01T15:00:00Z',
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.createEntry(gameId, newEntry);

      expect(result.location).toBeUndefined();
    });

    it('should handle all entry categories', async () => {
      const categories = ['Event', 'NPC', 'Location', 'Quest', 'Item'] as const;

      for (const category of categories) {
        const newEntry: CreateJournalEntryRequest = {
          title: `Test ${category}`,
          content: `Content for ${category}`,
          category: category,
        };

        const mockResponse: JournalEntry = {
          id: `entry-${category}`,
          ...newEntry,
          timestamp: '2024-01-01T10:00:00Z',
          created_at: '2024-01-01T10:00:00Z',
        };

        (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
          mockResponse
        );

        const result = await journalApiService.createEntry(gameId, newEntry);

        expect(result.category).toBe(category);
      }
    });

    it('should propagate creation errors', async () => {
      const newEntry: CreateJournalEntryRequest = {
        title: 'Test',
        content: 'Content',
        category: 'Event',
      };

      const error = new Error('Creation failed');
      (mockApiService.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        journalApiService.createEntry(gameId, newEntry)
      ).rejects.toThrow('Creation failed');
    });
  });

  describe('updateEntry', () => {
    const entryId = 'entry-1';

    it('should update an existing entry with all fields', async () => {
      const updates: UpdateJournalEntryRequest = {
        title: 'Updated Title',
        content: 'Updated content',
        category: 'Quest',
        location: 'New Location',
      };

      const mockResponse: JournalEntry = {
        id: entryId,
        title: 'Updated Title',
        content: 'Updated content',
        category: 'Quest',
        location: 'New Location',
        timestamp: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T16:00:00Z',
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.updateEntry(
        gameId,
        entryId,
        updates
      );

      expect(mockApiService.put).toHaveBeenCalledWith(
        '/api/game/game-123/journal/entry-1',
        updates
      );
      expect(result).toEqual(mockResponse);
      expect(result.updated_at).toBeDefined();
    });

    it('should update only title', async () => {
      const updates: UpdateJournalEntryRequest = {
        title: 'New Title',
      };

      const mockResponse: JournalEntry = {
        id: entryId,
        title: 'New Title',
        content: 'Original content',
        category: 'Event',
        timestamp: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T16:00:00Z',
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.updateEntry(
        gameId,
        entryId,
        updates
      );

      expect(result.title).toBe('New Title');
    });

    it('should update only content', async () => {
      const updates: UpdateJournalEntryRequest = {
        content: 'New content',
      };

      const mockResponse: JournalEntry = {
        id: entryId,
        title: 'Original Title',
        content: 'New content',
        category: 'Event',
        timestamp: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T16:00:00Z',
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.updateEntry(
        gameId,
        entryId,
        updates
      );

      expect(result.content).toBe('New content');
    });

    it('should update only category', async () => {
      const updates: UpdateJournalEntryRequest = {
        category: 'NPC',
      };

      const mockResponse: JournalEntry = {
        id: entryId,
        title: 'Original Title',
        content: 'Original content',
        category: 'NPC',
        timestamp: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T16:00:00Z',
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await journalApiService.updateEntry(
        gameId,
        entryId,
        updates
      );

      expect(result.category).toBe('NPC');
    });

    it('should propagate update errors', async () => {
      const updates: UpdateJournalEntryRequest = {
        title: 'New Title',
      };

      const error = new Error('Update failed');
      (mockApiService.put as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        journalApiService.updateEntry(gameId, entryId, updates)
      ).rejects.toThrow('Update failed');
    });
  });

  describe('deleteEntry', () => {
    const entryId = 'entry-1';

    it('should delete an entry', async () => {
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      await journalApiService.deleteEntry(gameId, entryId);

      expect(mockApiService.delete).toHaveBeenCalledWith(
        '/api/game/game-123/journal/entry-1'
      );
    });

    it('should handle deletion of non-existent entry', async () => {
      const error = new Error('Entry not found');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        journalApiService.deleteEntry(gameId, 'invalid-id')
      ).rejects.toThrow('Entry not found');
    });

    it('should propagate deletion errors', async () => {
      const error = new Error('Deletion failed');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        journalApiService.deleteEntry(gameId, entryId)
      ).rejects.toThrow('Deletion failed');
    });
  });

  describe('CRUD workflow', () => {
    it('should complete a full CRUD cycle', async () => {
      // Create
      const newEntry: CreateJournalEntryRequest = {
        title: 'Quest Started',
        content: 'We accepted the quest',
        category: 'Quest',
      };

      const createdEntry: JournalEntry = {
        id: 'entry-new',
        ...newEntry,
        timestamp: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T10:00:00Z',
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        createdEntry
      );

      const created = await journalApiService.createEntry(gameId, newEntry);
      expect(created.id).toBe('entry-new');

      // Read
      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        entries: [createdEntry],
      });

      const entries = await journalApiService.getEntries(gameId);
      expect(entries.entries).toHaveLength(1);

      // Update
      const updates: UpdateJournalEntryRequest = {
        content: 'We completed the quest',
      };

      const updatedEntry: JournalEntry = {
        ...createdEntry,
        content: 'We completed the quest',
        updated_at: '2024-01-01T11:00:00Z',
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        updatedEntry
      );

      const updated = await journalApiService.updateEntry(
        gameId,
        created.id,
        updates
      );
      expect(updated.content).toBe('We completed the quest');

      // Delete
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      await journalApiService.deleteEntry(gameId, created.id);

      expect(mockApiService.delete).toHaveBeenCalledWith(
        '/api/game/game-123/journal/entry-new'
      );
    });
  });
});
