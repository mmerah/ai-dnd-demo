/**
 * Game-specific API service
 *
 * Handles all game-related API calls with type-safe interfaces.
 * All types are auto-generated from backend Pydantic models.
 */

import { ApiService } from './ApiService.js';
import type { GameState } from '../../types/generated/GameState.js';
import type { NewGameRequest } from '../../types/generated/NewGameRequest.js';
import type { NewGameResponse } from '../../types/generated/NewGameResponse.js';
import type { PlayerActionRequest } from '../../types/generated/PlayerActionRequest.js';
import type { RemoveGameResponse } from '../../types/generated/RemoveGameResponse.js';
import type { ResumeGameResponse } from '../../types/generated/ResumeGameResponse.js';
import type { AcceptCombatSuggestionRequest } from '../../types/generated/AcceptCombatSuggestionRequest.js';
import type { AcceptCombatSuggestionResponse } from '../../types/generated/AcceptCombatSuggestionResponse.js';
import type { RequestAllySuggestionResponse } from '../../types/generated/RequestAllySuggestionResponse.js';
import type { EquipItemRequest } from '../../types/generated/EquipItemRequest.js';
import type { EquipItemResponse } from '../../types/generated/EquipItemResponse.js';
import type { ResolveNamesRequest } from '../../types/generated/ResolveNamesRequest.js';
import type { ResolveNamesResponse } from '../../types/generated/ResolveNamesResponse.js';

/**
 * Service for game-related API operations
 */
export class GameApiService {
  constructor(private readonly api: ApiService) {}

  /**
   * Create a new game
   */
  async createGame(
    scenarioId: string,
    characterId: string,
    contentPacks?: string[]
  ): Promise<NewGameResponse> {
    const request: NewGameRequest = {
      scenario_id: scenarioId,
      character_id: characterId,
    };

    // Add content packs if provided
    if (contentPacks && contentPacks.length > 0) {
      request.content_packs = contentPacks;
    }

    return this.api.post<NewGameResponse, NewGameRequest>('/api/game/new', request);
  }

  /**
   * Get game state by ID
   */
  async getGameState(gameId: string): Promise<GameState> {
    return this.api.get<GameState>(`/api/game/${gameId}`);
  }

  /**
   * Resume a saved game session
   * Backend endpoint is a simple acknowledgment for parity with legacy frontend
   */
  async resumeGame(gameId: string): Promise<ResumeGameResponse> {
    return this.api.post<ResumeGameResponse, never>(`/api/game/${gameId}/resume`, undefined as never);
  }

  /**
   * Send a player action
   */
  async sendAction(gameId: string, message: string): Promise<void> {
    const request: PlayerActionRequest = { message };
    return this.api.post<void, PlayerActionRequest>(
      `/api/game/${gameId}/action`,
      request
    );
  }

  /**
   * List all saved games
   * Backend returns array of GameState directly
   */
  async listGames(): Promise<Array<GameState>> {
    return this.api.get<Array<GameState>>('/api/games');
  }

  /**
   * Delete a saved game
   */
  async deleteGame(gameId: string): Promise<RemoveGameResponse> {
    return this.api.delete<RemoveGameResponse>(`/api/game/${gameId}`);
  }

  /**
   * Request a combat suggestion from the current allied NPC
   */
  async requestAllySuggestion(gameId: string): Promise<RequestAllySuggestionResponse> {
    return this.api.post<RequestAllySuggestionResponse, never>(
      `/api/game/${gameId}/ally/suggest`,
      undefined as never
    );
  }

  /**
   * Accept a combat suggestion from an allied NPC
   */
  async acceptCombatSuggestion(
    gameId: string,
    request: AcceptCombatSuggestionRequest
  ): Promise<AcceptCombatSuggestionResponse> {
    return this.api.post<AcceptCombatSuggestionResponse, AcceptCombatSuggestionRequest>(
      `/api/game/${gameId}/combat/suggestion/accept`,
      request
    );
  }

  /**
   * Equip or unequip an item for an entity (player or NPC)
   */
  async equipItem(
    gameId: string,
    request: EquipItemRequest
  ): Promise<EquipItemResponse> {
    return this.api.post<EquipItemResponse, EquipItemRequest>(
      `/api/game/${gameId}/equip`,
      request
    );
  }

  /**
   * Resolve display names for catalog items (spells, items, etc.)
   * Uses the game's content pack scope for name resolution.
   */
  async resolveNames(
    gameId: string,
    request: Omit<ResolveNamesRequest, 'game_id'>
  ): Promise<ResolveNamesResponse> {
    const fullRequest: ResolveNamesRequest = {
      game_id: gameId,
      ...request,
    };
    return this.api.post<ResolveNamesResponse, ResolveNamesRequest>(
      '/api/catalogs/resolve-names',
      fullRequest
    );
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<{ status: string }> {
    return this.api.get<{ status: string }>('/health');
  }
}
