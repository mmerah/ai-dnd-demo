/**
 * Journal API Service
 *
 * Handles all journal/chronicle-related API calls with type-safe interfaces.
 */

import { ApiService } from './ApiService.js';

export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  category: 'Event' | 'NPC' | 'Location' | 'Quest' | 'Item';
  location?: string;
  timestamp: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateJournalEntryRequest {
  title: string;
  content: string;
  category: 'Event' | 'NPC' | 'Location' | 'Quest' | 'Item';
  location?: string;
}

export interface UpdateJournalEntryRequest {
  title?: string;
  content?: string;
  category?: 'Event' | 'NPC' | 'Location' | 'Quest' | 'Item';
  location?: string;
}

export interface JournalEntriesResponse {
  entries: JournalEntry[];
}

/**
 * Service for journal-related API operations
 */
export class JournalApiService {
  constructor(private readonly api: ApiService) {}

  /**
   * Fetch all journal entries for a game
   */
  async getEntries(gameId: string): Promise<JournalEntriesResponse> {
    return this.api.get<JournalEntriesResponse>(`/api/game/${gameId}/journal`);
  }

  /**
   * Create a new journal entry
   */
  async createEntry(
    gameId: string,
    entry: CreateJournalEntryRequest
  ): Promise<JournalEntry> {
    return this.api.post<JournalEntry, CreateJournalEntryRequest>(
      `/api/game/${gameId}/journal`,
      entry
    );
  }

  /**
   * Update an existing journal entry
   */
  async updateEntry(
    gameId: string,
    entryId: string,
    updates: UpdateJournalEntryRequest
  ): Promise<JournalEntry> {
    return this.api.put<JournalEntry, UpdateJournalEntryRequest>(
      `/api/game/${gameId}/journal/${entryId}`,
      updates
    );
  }

  /**
   * Delete a journal entry
   */
  async deleteEntry(gameId: string, entryId: string): Promise<void> {
    return this.api.delete<void>(`/api/game/${gameId}/journal/${entryId}`);
  }
}
