/**
 * Game-specific API service
 *
 * Handles all game-related API calls with type-safe interfaces.
 */

import { ApiService } from './ApiService.js';
import { GameState } from '../../types/generated/GameState.js';

export interface CreateGameRequest {
  scenario_id: string;
  character_id: string;
}

export interface CreateGameResponse {
  game_id: string;
  game_state: GameState;
}

export interface SendActionRequest {
  action: string;
}

export interface GameListResponse {
  saves: Array<{
    game_id: string;
    scenario_name: string;
    character_name: string;
    last_saved: string;
    created_at: string;
  }>;
}

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
  ): Promise<CreateGameResponse> {
    return this.api.post<CreateGameResponse, CreateGameRequest>('/api/game/new', {
      scenario_id: scenarioId,
      character_id: characterId,
    });
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
  async sendAction(gameId: string, action: string): Promise<void> {
    return this.api.post<void, SendActionRequest>(
      `/api/game/${gameId}/action`,
      { action }
    );
  }

  /**
   * List all saved games
   */
  async listGames(): Promise<GameListResponse> {
    return this.api.get<GameListResponse>('/api/game/list');
  }

  /**
   * Delete a saved game
   */
  async deleteGame(gameId: string): Promise<void> {
    return this.api.delete<void>(`/api/game/${gameId}`);
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<{ status: string }> {
    return this.api.get<{ status: string }>('/health');
  }
}
