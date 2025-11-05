import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StateStore } from '../StateStore';
import type { GameState } from '../../../types/generated/GameState';
import { ValidationError, StateError } from '../../../types/errors';

describe('StateStore', () => {
  let stateStore: StateStore;

  const createValidGameState = (overrides?: Partial<GameState>): GameState => ({
    game_id: 'game-123',
    scenario_id: 'scenario-1',
    player: {
      id: 'player',
      name: 'Test Hero',
      hp: 50,
      max_hp: 50,
      level: 5,
      race: 'Human',
      class: 'Fighter',
      conditions: [],
    },
    location: {
      name: 'Test Location',
      description: 'A test location',
      exits: [],
      npcs: [],
    },
    party: {
      members: [
        {
          id: 'npc-1',
          name: 'Companion',
          hp: 30,
          max_hp: 30,
          level: 3,
          race: 'Elf',
          class: 'Ranger',
          conditions: [],
        },
      ],
    },
    conversation_history: [],
    ...overrides,
  } as GameState);

  beforeEach(() => {
    stateStore = new StateStore();
  });

  describe('initialization', () => {
    it('should initialize with default values', () => {
      expect(stateStore.getGameState()).toBeNull();
      expect(stateStore.getIsProcessing()).toBe(false);
      expect(stateStore.getSelectedMemberId()).toBe('player');
      expect(stateStore.getError()).toBeNull();
      expect(stateStore.getRightPanelView()).toBe('party');
    });

    it('should provide a snapshot of initial state', () => {
      const snapshot = stateStore.getSnapshot();

      expect(snapshot).toEqual({
        gameState: null,
        isProcessing: false,
        selectedMemberId: 'player',
        error: null,
      });
    });
  });

  describe('gameState', () => {
    it('should set and get game state', () => {
      const gameState = createValidGameState();

      stateStore.setGameState(gameState);

      expect(stateStore.getGameState()).toEqual(gameState);
    });

    it('should notify listeners on game state change', () => {
      const listener = vi.fn();
      stateStore.onGameStateChange(listener);

      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      expect(listener).toHaveBeenCalledWith(gameState);
    });

    it('should clear game state', () => {
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      stateStore.clearGameState();

      expect(stateStore.getGameState()).toBeNull();
    });

    it('should clear error when setting valid game state', () => {
      stateStore.setError('Test error');
      expect(stateStore.getError()).toBe('Test error');

      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      expect(stateStore.getError()).toBeNull();
    });
  });

  describe('game state validation', () => {
    it('should throw ValidationError if game_id is missing', () => {
      const invalidState = createValidGameState();
      (invalidState as any).game_id = '';

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'GameState missing game_id'
      );
    });

    it('should throw ValidationError if player is missing', () => {
      const invalidState = createValidGameState();
      (invalidState as any).player = null;

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'GameState missing player'
      );
    });

    it('should throw ValidationError if location is missing', () => {
      const invalidState = createValidGameState();
      (invalidState as any).location = null;

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'GameState missing location'
      );
    });

    it('should throw ValidationError if player HP is negative', () => {
      const invalidState = createValidGameState();
      invalidState.player.hp = -1;

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'Player HP cannot be negative'
      );
    });

    it('should allow player HP of 0', () => {
      const validState = createValidGameState();
      validState.player.hp = 0;

      expect(() => stateStore.setGameState(validState)).not.toThrow();
    });

    it('should throw ValidationError if player level is less than 1', () => {
      const invalidState = createValidGameState();
      invalidState.player.level = 0;

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'Player level must be between 1 and 20'
      );
    });

    it('should throw ValidationError if player level is greater than 20', () => {
      const invalidState = createValidGameState();
      invalidState.player.level = 21;

      expect(() => stateStore.setGameState(invalidState)).toThrow(
        ValidationError
      );
      expect(() => stateStore.setGameState(invalidState)).toThrow(
        'Player level must be between 1 and 20'
      );
    });

    it('should allow player level of 1 and 20', () => {
      const state1 = createValidGameState();
      state1.player.level = 1;

      const state20 = createValidGameState();
      state20.player.level = 20;

      expect(() => stateStore.setGameState(state1)).not.toThrow();
      expect(() => stateStore.setGameState(state20)).not.toThrow();
    });
  });

  describe('isProcessing', () => {
    it('should set and get processing state', () => {
      stateStore.setIsProcessing(true);
      expect(stateStore.getIsProcessing()).toBe(true);

      stateStore.setIsProcessing(false);
      expect(stateStore.getIsProcessing()).toBe(false);
    });

    it('should notify listeners on processing change', () => {
      const listener = vi.fn();
      stateStore.onProcessingChange(listener);

      stateStore.setIsProcessing(true);

      expect(listener).toHaveBeenCalledWith(true);
    });
  });

  describe('selectedMemberId', () => {
    it('should set and get selected member ID', () => {
      stateStore.setSelectedMemberId('player');
      expect(stateStore.getSelectedMemberId()).toBe('player');
    });

    it('should notify listeners on selected member change', () => {
      const listener = vi.fn();
      stateStore.onSelectedMemberChange(listener);

      // Change to different value (initial is 'player')
      stateStore.setSelectedMemberId('other-id');

      expect(listener).toHaveBeenCalledWith('other-id');
    });

    it('should validate member ID against game state', () => {
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      // Valid IDs: 'player' and 'npc-1'
      expect(() => stateStore.setSelectedMemberId('player')).not.toThrow();
      expect(() => stateStore.setSelectedMemberId('npc-1')).not.toThrow();
    });

    it('should throw ValidationError for invalid member ID', () => {
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      expect(() => stateStore.setSelectedMemberId('invalid-id')).toThrow(
        ValidationError
      );
      expect(() => stateStore.setSelectedMemberId('invalid-id')).toThrow(
        'Invalid member ID: invalid-id'
      );
    });

    it('should allow setting member ID when no game state', () => {
      expect(() => stateStore.setSelectedMemberId('any-id')).not.toThrow();
    });
  });

  describe('error', () => {
    it('should set and get error', () => {
      stateStore.setError('Test error');
      expect(stateStore.getError()).toBe('Test error');
    });

    it('should clear error', () => {
      stateStore.setError('Test error');
      stateStore.clearError();
      expect(stateStore.getError()).toBeNull();
    });

    it('should notify listeners on error change', () => {
      const listener = vi.fn();
      stateStore.onErrorChange(listener);

      stateStore.setError('Test error');

      expect(listener).toHaveBeenCalledWith('Test error');
    });

    it('should notify listeners on error clear', () => {
      const listener = vi.fn();
      stateStore.setError('Test error');
      stateStore.onErrorChange(listener);

      stateStore.clearError();

      expect(listener).toHaveBeenCalledWith(null);
    });
  });

  describe('rightPanelView', () => {
    it('should set and get right panel view', () => {
      stateStore.setRightPanelView('character-sheet');
      expect(stateStore.getRightPanelView()).toBe('character-sheet');

      stateStore.setRightPanelView('inventory');
      expect(stateStore.getRightPanelView()).toBe('inventory');

      stateStore.setRightPanelView('party');
      expect(stateStore.getRightPanelView()).toBe('party');
    });

    it('should notify listeners on right panel view change', () => {
      const listener = vi.fn();
      stateStore.onRightPanelViewChange(listener);

      stateStore.setRightPanelView('character-sheet');

      expect(listener).toHaveBeenCalledWith('character-sheet');
    });
  });

  describe('subscribeAll', () => {
    it('should subscribe to all state changes', () => {
      const callbacks = {
        onGameState: vi.fn(),
        onProcessing: vi.fn(),
        onSelectedMember: vi.fn(),
        onError: vi.fn(),
        onRightPanelView: vi.fn(),
      };

      stateStore.subscribeAll(callbacks);

      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      stateStore.setIsProcessing(true);
      stateStore.setSelectedMemberId('npc-1'); // Change from default 'player'
      stateStore.setError('Test error');
      stateStore.setRightPanelView('character-sheet');

      expect(callbacks.onGameState).toHaveBeenCalledWith(gameState);
      expect(callbacks.onProcessing).toHaveBeenCalledWith(true);
      expect(callbacks.onSelectedMember).toHaveBeenCalledWith('npc-1');
      expect(callbacks.onError).toHaveBeenCalledWith('Test error');
      expect(callbacks.onRightPanelView).toHaveBeenCalledWith('character-sheet');
    });

    it('should allow partial subscription', () => {
      const onGameState = vi.fn();
      const onError = vi.fn();

      stateStore.subscribeAll({
        onGameState,
        onError,
      });

      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      stateStore.setError('Test error');
      stateStore.setIsProcessing(true); // This should not throw

      expect(onGameState).toHaveBeenCalledWith(gameState);
      expect(onError).toHaveBeenCalledWith('Test error');
    });

    it('should return unsubscribe function that cleans up all subscriptions', () => {
      const callbacks = {
        onGameState: vi.fn(),
        onProcessing: vi.fn(),
      };

      const unsubscribe = stateStore.subscribeAll(callbacks);

      // Verify subscriptions work
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      expect(callbacks.onGameState).toHaveBeenCalledTimes(1);

      // Unsubscribe
      unsubscribe();

      // Verify callbacks are no longer called
      const gameState2 = createValidGameState({ game_id: 'game-456' });
      stateStore.setGameState(gameState2);
      expect(callbacks.onGameState).toHaveBeenCalledTimes(1); // Still 1, not 2
    });
  });

  describe('reset', () => {
    it('should reset all state to default values', () => {
      // Set non-default values
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      stateStore.setIsProcessing(true);
      stateStore.setSelectedMemberId('npc-1');
      stateStore.setError('Test error');
      stateStore.setRightPanelView('character-sheet');

      // Reset
      stateStore.reset();

      // Verify all values are back to defaults
      expect(stateStore.getGameState()).toBeNull();
      expect(stateStore.getIsProcessing()).toBe(false);
      expect(stateStore.getSelectedMemberId()).toBe('player');
      expect(stateStore.getError()).toBeNull();
      expect(stateStore.getRightPanelView()).toBe('party');
    });

    it('should notify all listeners on reset', () => {
      const callbacks = {
        onGameState: vi.fn(),
        onProcessing: vi.fn(),
        onSelectedMember: vi.fn(),
        onError: vi.fn(),
        onRightPanelView: vi.fn(),
      };

      // Set non-default values
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      stateStore.setIsProcessing(true);
      stateStore.setSelectedMemberId('npc-1'); // Change from default 'player'
      stateStore.setError('Test error');
      stateStore.setRightPanelView('inventory');

      // Subscribe after setting values
      stateStore.subscribeAll(callbacks);

      // Reset
      stateStore.reset();

      // Verify notifications
      expect(callbacks.onGameState).toHaveBeenCalledWith(null);
      expect(callbacks.onProcessing).toHaveBeenCalledWith(false);
      expect(callbacks.onSelectedMember).toHaveBeenCalledWith('player');
      expect(callbacks.onError).toHaveBeenCalledWith(null);
      expect(callbacks.onRightPanelView).toHaveBeenCalledWith('party');
    });
  });

  describe('getSnapshot', () => {
    it('should return current state snapshot', () => {
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);
      stateStore.setIsProcessing(true);
      stateStore.setSelectedMemberId('npc-1');
      stateStore.setError('Test error');

      const snapshot = stateStore.getSnapshot();

      expect(snapshot).toEqual({
        gameState,
        isProcessing: true,
        selectedMemberId: 'npc-1',
        error: 'Test error',
      });
    });

    it('should return immutable snapshot', () => {
      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      const snapshot1 = stateStore.getSnapshot();
      const snapshot2 = stateStore.getSnapshot();

      expect(snapshot1).toEqual(snapshot2);
      expect(snapshot1.gameState).toBe(snapshot2.gameState); // Same reference
    });
  });

  describe('unsubscribe behavior', () => {
    it('should properly unsubscribe from individual subscriptions', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      const unsub1 = stateStore.onGameStateChange(listener1);
      const unsub2 = stateStore.onGameStateChange(listener2);

      const gameState = createValidGameState();
      stateStore.setGameState(gameState);

      expect(listener1).toHaveBeenCalledTimes(1);
      expect(listener2).toHaveBeenCalledTimes(1);

      // Unsubscribe first listener
      unsub1();

      const gameState2 = createValidGameState({ game_id: 'game-456' });
      stateStore.setGameState(gameState2);

      expect(listener1).toHaveBeenCalledTimes(1); // Still 1
      expect(listener2).toHaveBeenCalledTimes(2); // Now 2
    });
  });
});
