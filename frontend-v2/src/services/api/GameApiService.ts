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
import type { AcceptCombatSuggestionRequest } from '../../types/generated/AcceptCombatSuggestionRequest.js';
import type { AcceptCombatSuggestionResponse } from '../../types/generated/AcceptCombatSuggestionResponse.js';

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
    characterId: string
  ): Promise<NewGameResponse> {
    const request: NewGameRequest = {
      scenario_id: scenarioId,
      character_id: characterId,
    };
    return this.api.post<NewGameResponse, NewGameRequest>('/api/game/new', request);
  }

  /**
   * Get game state by ID
   */
  async getGameState(gameId: string): Promise<GameState> {
    return this.api.get<GameState>(`/api/game/${gameId}`);
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
   * Check API health
   */
  async checkHealth(): Promise<{ status: string }> {
    return this.api.get<{ status: string }>('/health');
  }
}
