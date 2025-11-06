/**
 * Journal API Service
 *
 * Handles all journal/chronicle-related API calls with type-safe interfaces.
 * All types are auto-generated from backend Pydantic models.
 */

import { ApiService } from './ApiService.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';
import type { CreateJournalEntryRequest } from '../../types/generated/CreateJournalEntryRequest.js';
import type { CreateJournalEntryResponse } from '../../types/generated/CreateJournalEntryResponse.js';
import type { UpdateJournalEntryRequest } from '../../types/generated/UpdateJournalEntryRequest.js';
import type { UpdateJournalEntryResponse } from '../../types/generated/UpdateJournalEntryResponse.js';
import type { DeleteJournalEntryResponse } from '../../types/generated/DeleteJournalEntryResponse.js';

/**
 * Service for journal-related API operations
 */
export class JournalApiService {
  constructor(private readonly api: ApiService) {}

  /**
   * Fetch all journal entries for a game
   * Backend returns array of PlayerJournalEntry directly
   */
  async getEntries(gameId: string): Promise<Array<PlayerJournalEntry>> {
    return this.api.get<Array<PlayerJournalEntry>>(`/api/game/${gameId}/journal`);
  }

  /**
   * Get a specific journal entry
   */
  async getEntry(gameId: string, entryId: string): Promise<PlayerJournalEntry> {
    return this.api.get<PlayerJournalEntry>(`/api/game/${gameId}/journal/${entryId}`);
  }

  /**
   * Create a new journal entry
   */
  async createEntry(
    gameId: string,
    request: CreateJournalEntryRequest
  ): Promise<CreateJournalEntryResponse> {
    return this.api.post<CreateJournalEntryResponse, CreateJournalEntryRequest>(
      `/api/game/${gameId}/journal`,
      request
    );
  }

  /**
   * Update an existing journal entry
   */
  async updateEntry(
    gameId: string,
    entryId: string,
    request: UpdateJournalEntryRequest
  ): Promise<UpdateJournalEntryResponse> {
    return this.api.put<UpdateJournalEntryResponse, UpdateJournalEntryRequest>(
      `/api/game/${gameId}/journal/${entryId}`,
      request
    );
  }

  /**
   * Delete a journal entry
   */
  async deleteEntry(gameId: string, entryId: string): Promise<DeleteJournalEntryResponse> {
    return this.api.delete<DeleteJournalEntryResponse>(`/api/game/${gameId}/journal/${entryId}`);
  }

  /**
   * Toggle pin status of a journal entry
   */
  async togglePin(gameId: string, entryId: string): Promise<UpdateJournalEntryResponse> {
    return this.api.patch<UpdateJournalEntryResponse>(
      `/api/game/${gameId}/journal/${entryId}/pin`,
      {}
    );
  }
}
