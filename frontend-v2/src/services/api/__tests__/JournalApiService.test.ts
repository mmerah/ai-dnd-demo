import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JournalApiService } from '../JournalApiService';
import { ApiService } from '../ApiService';
import type { PlayerJournalEntry } from '../../../types/generated/PlayerJournalEntry';
import type { CreateJournalEntryRequest } from '../../../types/generated/CreateJournalEntryRequest';
import type { CreateJournalEntryResponse } from '../../../types/generated/CreateJournalEntryResponse';
import type { UpdateJournalEntryRequest } from '../../../types/generated/UpdateJournalEntryRequest';
import type { UpdateJournalEntryResponse } from '../../../types/generated/UpdateJournalEntryResponse';
import type { DeleteJournalEntryResponse } from '../../../types/generated/DeleteJournalEntryResponse';

// Mock ApiService
vi.mock('../ApiService');

// Helper to create minimal mock PlayerJournalEntry for testing
function createMockEntry(overrides?: Partial<PlayerJournalEntry>): PlayerJournalEntry {
  return {
    entry_id: 'entry-1',
    content: 'Test journal entry content',
    tags: ['combat', 'important'],
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z',
    location_id: null,
    npc_ids: [],
    pinned: false,
    ...overrides,
  };
}

describe('JournalApiService', () => {
  let journalApiService: JournalApiService;
  let mockApiService: ApiService;
  const gameId = 'game-123';

  beforeEach(() => {
    mockApiService = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    } as unknown as ApiService;

    journalApiService = new JournalApiService(mockApiService);
  });

  describe('getEntries', () => {
    it('should fetch all journal entries for a game', async () => {
      const mockEntries: PlayerJournalEntry[] = [
        createMockEntry({
          entry_id: 'entry-1',
          content: 'We met the mayor of Phandalin',
          tags: ['npc', 'quest'],
          location_id: 'phandalin',
        }),
        createMockEntry({
          entry_id: 'entry-2',
          content: 'Discovered a magic sword in the ruins',
          tags: ['item', 'magic'],
          pinned: true,
        }),
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEntries);

      const result = await journalApiService.getEntries(gameId);

      expect(mockApiService.get).toHaveBeenCalledWith('/api/game/game-123/journal');
      expect(result).toEqual(mockEntries);
      expect(result).toHaveLength(2);
    });

    it('should handle empty journal', async () => {
      const mockEntries: PlayerJournalEntry[] = [];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEntries);

      const result = await journalApiService.getEntries(gameId);

      expect(result).toHaveLength(0);
    });

    it('should propagate fetch errors', async () => {
      const error = new Error('Fetch failed');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.getEntries(gameId)).rejects.toThrow('Fetch failed');
    });
  });

  describe('getEntry', () => {
    it('should fetch a specific journal entry', async () => {
      const mockEntry = createMockEntry({
        entry_id: 'entry-1',
        content: 'Specific entry content',
      });

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEntry);

      const result = await journalApiService.getEntry(gameId, 'entry-1');

      expect(mockApiService.get).toHaveBeenCalledWith('/api/game/game-123/journal/entry-1');
      expect(result).toEqual(mockEntry);
    });

    it('should handle entry not found', async () => {
      const error = new Error('Entry not found');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.getEntry(gameId, 'invalid-id')).rejects.toThrow('Entry not found');
    });
  });

  describe('createEntry', () => {
    it('should create a new journal entry', async () => {
      const request: CreateJournalEntryRequest = {
        content: 'We fought off a goblin ambush',
        tags: ['combat', 'goblins'],
      };

      const createdEntry = createMockEntry({
        entry_id: 'entry-3',
        content: request.content,
        tags: request.tags,
      });

      const mockResponse: CreateJournalEntryResponse = {
        entry: createdEntry,
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.createEntry(gameId, request);

      expect(mockApiService.post).toHaveBeenCalledWith('/api/game/game-123/journal', request);
      expect(result).toEqual(mockResponse);
      expect(result.entry.content).toBe(request.content);
      expect(result.entry.tags).toEqual(request.tags);
    });

    it('should create entry without tags', async () => {
      const request: CreateJournalEntryRequest = {
        content: 'Something interesting happened',
        tags: [],
      };

      const createdEntry = createMockEntry({
        entry_id: 'entry-4',
        content: request.content,
        tags: [],
      });

      const mockResponse: CreateJournalEntryResponse = {
        entry: createdEntry,
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.createEntry(gameId, request);

      expect(result.entry.tags).toEqual([]);
    });

    it('should propagate creation errors', async () => {
      const request: CreateJournalEntryRequest = {
        content: 'Test content',
        tags: [],
      };

      const error = new Error('Creation failed');
      (mockApiService.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.createEntry(gameId, request)).rejects.toThrow('Creation failed');
    });
  });

  describe('updateEntry', () => {
    const entryId = 'entry-1';

    it('should update an existing entry', async () => {
      const request: UpdateJournalEntryRequest = {
        content: 'Updated content',
        tags: ['updated', 'tags'],
      };

      const updatedEntry = createMockEntry({
        entry_id: entryId,
        content: request.content,
        tags: request.tags,
        updated_at: '2024-01-01T16:00:00Z',
      });

      const mockResponse: UpdateJournalEntryResponse = {
        entry: updatedEntry,
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.updateEntry(gameId, entryId, request);

      expect(mockApiService.put).toHaveBeenCalledWith('/api/game/game-123/journal/entry-1', request);
      expect(result).toEqual(mockResponse);
      expect(result.entry.content).toBe(request.content);
      expect(result.entry.updated_at).toBeDefined();
    });

    it('should update entry with empty tags', async () => {
      const request: UpdateJournalEntryRequest = {
        content: 'Content without tags',
        tags: [],
      };

      const updatedEntry = createMockEntry({
        entry_id: entryId,
        content: request.content,
        tags: [],
        updated_at: '2024-01-01T16:00:00Z',
      });

      const mockResponse: UpdateJournalEntryResponse = {
        entry: updatedEntry,
      };

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.updateEntry(gameId, entryId, request);

      expect(result.entry.tags).toEqual([]);
    });

    it('should propagate update errors', async () => {
      const request: UpdateJournalEntryRequest = {
        content: 'New content',
        tags: [],
      };

      const error = new Error('Update failed');
      (mockApiService.put as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.updateEntry(gameId, entryId, request)).rejects.toThrow('Update failed');
    });
  });

  describe('deleteEntry', () => {
    const entryId = 'entry-1';

    it('should delete an entry', async () => {
      const mockResponse: DeleteJournalEntryResponse = {
        success: true,
        entry_id: entryId,
      };

      (mockApiService.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.deleteEntry(gameId, entryId);

      expect(mockApiService.delete).toHaveBeenCalledWith('/api/game/game-123/journal/entry-1');
      expect(result.success).toBe(true);
      expect(result.entry_id).toBe(entryId);
    });

    it('should handle deletion of non-existent entry', async () => {
      const error = new Error('Entry not found');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.deleteEntry(gameId, 'invalid-id')).rejects.toThrow('Entry not found');
    });

    it('should propagate deletion errors', async () => {
      const error = new Error('Deletion failed');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.deleteEntry(gameId, entryId)).rejects.toThrow('Deletion failed');
    });
  });

  describe('togglePin', () => {
    const entryId = 'entry-1';

    it('should toggle pin status to pinned', async () => {
      const mockEntry = createMockEntry({
        entry_id: entryId,
        pinned: true,
      });

      const mockResponse: UpdateJournalEntryResponse = {
        entry: mockEntry,
      };

      (mockApiService.patch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.togglePin(gameId, entryId);

      expect(mockApiService.patch).toHaveBeenCalledWith('/api/game/game-123/journal/entry-1/pin', {});
      expect(result.entry.pinned).toBe(true);
    });

    it('should toggle pin status to unpinned', async () => {
      const mockEntry = createMockEntry({
        entry_id: entryId,
        pinned: false,
      });

      const mockResponse: UpdateJournalEntryResponse = {
        entry: mockEntry,
      };

      (mockApiService.patch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await journalApiService.togglePin(gameId, entryId);

      expect(result.entry.pinned).toBe(false);
    });

    it('should propagate toggle errors', async () => {
      const error = new Error('Toggle failed');
      (mockApiService.patch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(journalApiService.togglePin(gameId, entryId)).rejects.toThrow('Toggle failed');
    });
  });

  describe('CRUD workflow', () => {
    it('should complete a full CRUD cycle with pin', async () => {
      // Create
      const newRequest: CreateJournalEntryRequest = {
        content: 'We accepted the quest',
        tags: ['quest', 'main-story'],
      };

      const createdEntry = createMockEntry({
        entry_id: 'entry-new',
        content: newRequest.content,
        tags: newRequest.tags,
      });

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        entry: createdEntry,
      });

      const created = await journalApiService.createEntry(gameId, newRequest);
      expect(created.entry.entry_id).toBe('entry-new');

      // Read all
      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce([createdEntry]);

      const entries = await journalApiService.getEntries(gameId);
      expect(entries).toHaveLength(1);

      // Update
      const updateRequest: UpdateJournalEntryRequest = {
        content: 'We completed the quest',
        tags: ['quest', 'main-story', 'completed'],
      };

      const updatedEntry = createMockEntry({
        ...createdEntry,
        content: updateRequest.content,
        tags: updateRequest.tags,
        updated_at: '2024-01-01T11:00:00Z',
      });

      (mockApiService.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        entry: updatedEntry,
      });

      const updated = await journalApiService.updateEntry(gameId, created.entry.entry_id, updateRequest);
      expect(updated.entry.content).toBe('We completed the quest');

      // Toggle pin
      const pinnedEntry = createMockEntry({
        ...updatedEntry,
        pinned: true,
      });

      (mockApiService.patch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        entry: pinnedEntry,
      });

      const pinned = await journalApiService.togglePin(gameId, created.entry.entry_id);
      expect(pinned.entry.pinned).toBe(true);

      // Delete
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        success: true,
        entry_id: created.entry.entry_id,
      });

      const deleted = await journalApiService.deleteEntry(gameId, created.entry.entry_id);
      expect(deleted.success).toBe(true);

      expect(mockApiService.delete).toHaveBeenCalledWith('/api/game/game-123/journal/entry-new');
    });
  });
});
