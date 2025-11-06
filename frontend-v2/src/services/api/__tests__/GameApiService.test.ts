import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GameApiService } from '../GameApiService';
import { ApiService } from '../ApiService';
import type { GameState } from '../../../types/generated/GameState';

// Mock ApiService
vi.mock('../ApiService');

// Helper to create minimal mock GameState for testing
function createMockGameState(overrides?: Partial<GameState>): GameState {
  return {
    game_id: 'test-game-123',
    character: {} as any,
    scenario_id: 'test-scenario',
    scenario_title: 'Test Scenario',
    scenario_instance: {} as any,
    ...overrides,
  } as GameState;
}

describe('GameApiService', () => {
  let gameApiService: GameApiService;
  let mockApiService: ApiService;

  beforeEach(() => {
    mockApiService = {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
    } as unknown as ApiService;

    gameApiService = new GameApiService(mockApiService);
  });

  describe('createGame', () => {
    it('should create a new game with scenario and character IDs', async () => {
      const mockResponse = {
        game_id: 'game-123',
      };

      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await gameApiService.createGame('scenario-1', 'char-1');

      expect(mockApiService.post).toHaveBeenCalledWith('/api/game/new', {
        scenario_id: 'scenario-1',
        character_id: 'char-1',
      });
      expect(result).toEqual(mockResponse);
    });

    it('should propagate API errors', async () => {
      const error = new Error('Creation failed');
      (mockApiService.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        gameApiService.createGame('scenario-1', 'char-1')
      ).rejects.toThrow('Creation failed');
    });
  });

  describe('getGameState', () => {
    it('should fetch game state by ID', async () => {
      const mockGameState = createMockGameState({
        game_id: 'game-123',
        scenario_id: 'scenario-1',
      });

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockGameState
      );

      const result = await gameApiService.getGameState('game-123');

      expect(mockApiService.get).toHaveBeenCalledWith('/api/game/game-123');
      expect(result).toEqual(mockGameState);
    });

    it('should handle game not found error', async () => {
      const error = new Error('Game not found');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(gameApiService.getGameState('invalid-id')).rejects.toThrow(
        'Game not found'
      );
    });
  });

  describe('sendAction', () => {
    it('should send player action to game', async () => {
      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      await gameApiService.sendAction('game-123', 'Look around');

      expect(mockApiService.post).toHaveBeenCalledWith(
        '/api/game/game-123/action',
        { message: 'Look around' }
      );
    });

    it('should handle action with special characters', async () => {
      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      const action = 'Say "Hello!" to @NPC_NAME';
      await gameApiService.sendAction('game-123', action);

      expect(mockApiService.post).toHaveBeenCalledWith(
        '/api/game/game-123/action',
        { message: action }
      );
    });

    it('should propagate action errors', async () => {
      const error = new Error('Action failed');
      (mockApiService.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(
        gameApiService.sendAction('game-123', 'invalid action')
      ).rejects.toThrow('Action failed');
    });
  });

  describe('listGames', () => {
    it('should fetch list of saved games', async () => {
      const mockList = [
        createMockGameState({
          game_id: 'game-1',
          scenario_title: 'The Lost Mine',
          last_saved: '2024-01-01T12:00:00Z',
          created_at: '2024-01-01T10:00:00Z',
        }),
        createMockGameState({
          game_id: 'game-2',
          scenario_title: 'Dragon Quest',
          last_saved: '2024-01-02T12:00:00Z',
          created_at: '2024-01-02T10:00:00Z',
        }),
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockList
      );

      const result = await gameApiService.listGames();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/games');
      expect(result).toEqual(mockList);
      expect(result).toHaveLength(2);
    });

    it('should handle empty game list', async () => {
      const mockList: any[] = [];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockList
      );

      const result = await gameApiService.listGames();

      expect(result).toHaveLength(0);
    });

    it('should propagate list fetch errors', async () => {
      const error = new Error('Fetch failed');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(gameApiService.listGames()).rejects.toThrow('Fetch failed');
    });
  });

  describe('deleteGame', () => {
    it('should delete a game by ID', async () => {
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      await gameApiService.deleteGame('game-123');

      expect(mockApiService.delete).toHaveBeenCalledWith('/api/game/game-123');
    });

    it('should handle delete errors', async () => {
      const error = new Error('Delete failed');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(gameApiService.deleteGame('game-123')).rejects.toThrow(
        'Delete failed'
      );
    });

    it('should handle deletion of non-existent game', async () => {
      const error = new Error('Game not found');
      (mockApiService.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(gameApiService.deleteGame('invalid-id')).rejects.toThrow(
        'Game not found'
      );
    });
  });

  describe('checkHealth', () => {
    it('should check API health status', async () => {
      const mockHealth = { status: 'ok' };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockHealth
      );

      const result = await gameApiService.checkHealth();

      expect(mockApiService.get).toHaveBeenCalledWith('/health');
      expect(result).toEqual(mockHealth);
      expect(result.status).toBe('ok');
    });

    it('should handle unhealthy status', async () => {
      const mockHealth = { status: 'error' };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockHealth
      );

      const result = await gameApiService.checkHealth();

      expect(result.status).toBe('error');
    });

    it('should handle health check failures', async () => {
      const error = new Error('Health check failed');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(gameApiService.checkHealth()).rejects.toThrow(
        'Health check failed'
      );
    });
  });

  describe('integration patterns', () => {
    it('should handle sequential operations', async () => {
      // Create game
      const createResponse = {
        game_id: 'new-game',
        game_state: createMockGameState({ game_id: 'new-game' }),
      };
      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        createResponse
      );

      const created = await gameApiService.createGame('scenario-1', 'char-1');

      // Send action
      (mockApiService.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        undefined
      );

      await gameApiService.sendAction(created.game_id, 'Look around');

      // Get state
      const mockState = createMockGameState({ game_id: created.game_id });
      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockState
      );

      const state = await gameApiService.getGameState(created.game_id);

      expect(state.game_id).toBe(created.game_id);
    });

    it('should handle parallel operations', async () => {
      // List games and check health in parallel
      const mockList: any[] = [];
      const mockHealth = { status: 'ok' };

      (mockApiService.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce(mockList)
        .mockResolvedValueOnce(mockHealth);

      const [games, health] = await Promise.all([
        gameApiService.listGames(),
        gameApiService.checkHealth(),
      ]);

      expect(games).toHaveLength(0);
      expect(health.status).toBe('ok');
    });
  });

  describe('error handling patterns', () => {
    it('should preserve error types from ApiService', async () => {
      const apiError = new Error('API Error');
      apiError.name = 'ApiError';
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        apiError
      );

      try {
        await gameApiService.getGameState('game-123');
        expect.fail('Should have thrown error');
      } catch (error) {
        expect(error).toBe(apiError);
      }
    });

    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      networkError.name = 'NetworkError';
      (mockApiService.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        networkError
      );

      try {
        await gameApiService.sendAction('game-123', 'action');
        expect.fail('Should have thrown error');
      } catch (error) {
        expect(error).toBe(networkError);
      }
    });
  });
});
