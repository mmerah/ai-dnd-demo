/**
 * Centralized state management using Observable pattern
 *
 * Single source of truth for application state with type-safe subscriptions.
 * Validates state at boundaries to fail fast on invalid data.
 */

import { Observable, Unsubscribe } from './Observable.js';
import { GameState } from '../../types/generated/GameState.js';
import { StateError, ValidationError } from '../../types/errors.js';

export interface AppState {
  gameState: GameState | null;
  isProcessing: boolean;
  selectedMemberId: string;
  error: string | null;
}

/**
 * Validates that a game state object has the required properties
 */
function validateGameState(state: GameState): void {
  if (!state.game_id) {
    throw new ValidationError('GameState missing game_id');
  }

  if (!state.character) {
    throw new ValidationError('GameState missing character');
  }

  if (!state.location) {
    throw new ValidationError('GameState missing location');
  }

  const hp = state.character.state.hit_points.current;
  if (hp < 0) {
    throw new ValidationError('Character HP cannot be negative');
  }

  const level = state.character.state.level;
  if (level !== undefined && (level < 1 || level > 20)) {
    throw new ValidationError('Character level must be between 1 and 20');
  }
}

/**
 * StateStore manages all application state using Observables
 */
export type RightPanelView = 'party' | 'character-sheet' | 'inventory';

export class StateStore {
  private gameState: Observable<GameState | null>;
  private isProcessing: Observable<boolean>;
  private selectedMemberId: Observable<string>;
  private error: Observable<string | null>;
  private rightPanelView: Observable<RightPanelView>;

  constructor() {
    this.gameState = new Observable<GameState | null>(null);
    this.isProcessing = new Observable<boolean>(false);
    // Start with empty string - will be set to character instance_id when game loads
    this.selectedMemberId = new Observable<string>('');
    this.error = new Observable<string | null>(null);
    this.rightPanelView = new Observable<RightPanelView>('party');
  }

  // ==================== Observable Getters ====================
  // Public getters for subscribing to observables in components

  get gameState$(): Observable<GameState | null> {
    return this.gameState;
  }

  get isProcessing$(): Observable<boolean> {
    return this.isProcessing;
  }

  get selectedMemberId$(): Observable<string> {
    return this.selectedMemberId;
  }

  get error$(): Observable<string | null> {
    return this.error;
  }

  get rightPanelView$(): Observable<RightPanelView> {
    return this.rightPanelView;
  }

  // ==================== Game State ====================

  getGameState(): GameState | null {
    return this.gameState.get();
  }

  setGameState(state: GameState): void {
    try {
      validateGameState(state);
      this.gameState.set(state);
      this.clearError(); // Clear any previous errors on successful state update
    } catch (error) {
      if (error instanceof ValidationError) {
        throw error;
      }
      throw new StateError('Failed to set game state', error);
    }
  }

  clearGameState(): void {
    this.gameState.set(null);
  }

  onGameStateChange(callback: (state: GameState | null) => void): Unsubscribe {
    return this.gameState.subscribe(callback);
  }

  // ==================== Processing State ====================

  getIsProcessing(): boolean {
    return this.isProcessing.get();
  }

  setIsProcessing(processing: boolean): void {
    this.isProcessing.set(processing);
  }

  onProcessingChange(callback: (processing: boolean) => void): Unsubscribe {
    return this.isProcessing.subscribe(callback);
  }

  // ==================== Selected Member ====================

  getSelectedMemberId(): string {
    return this.selectedMemberId.get();
  }

  setSelectedMemberId(memberId: string): void {
    const state = this.gameState.get();
    if (state) {
      // Validate that the member ID exists in the game
      // Valid IDs are: player character's instance_id + all party member IDs
      const validIds = [state.character.instance_id, ...(state.party?.member_ids ?? [])];
      if (!validIds.includes(memberId)) {
        throw new ValidationError(
          `Invalid member ID: ${memberId}. Must be one of: ${validIds.join(', ')}`
        );
      }
    }
    this.selectedMemberId.set(memberId);
  }

  onSelectedMemberChange(callback: (memberId: string) => void): Unsubscribe {
    return this.selectedMemberId.subscribe(callback);
  }

  // ==================== Error State ====================

  getError(): string | null {
    return this.error.get();
  }

  setError(error: string): void {
    this.error.set(error);
  }

  clearError(): void {
    this.error.set(null);
  }

  onErrorChange(callback: (error: string | null) => void): Unsubscribe {
    return this.error.subscribe(callback);
  }

  // ==================== Right Panel View ====================

  getRightPanelView(): RightPanelView {
    return this.rightPanelView.get();
  }

  setRightPanelView(view: RightPanelView): void {
    this.rightPanelView.set(view);
  }

  onRightPanelViewChange(callback: (view: RightPanelView) => void): Unsubscribe {
    return this.rightPanelView.subscribe(callback);
  }

  // ==================== Utility Methods ====================

  /**
   * Get a snapshot of the entire application state
   */
  getSnapshot(): AppState {
    return {
      gameState: this.gameState.get(),
      isProcessing: this.isProcessing.get(),
      selectedMemberId: this.selectedMemberId.get(),
      error: this.error.get(),
    };
  }

  /**
   * Subscribe to all state changes
   * Returns a single unsubscribe function that cleans up all subscriptions
   */
  subscribeAll(callbacks: {
    onGameState?: (state: GameState | null) => void;
    onProcessing?: (processing: boolean) => void;
    onSelectedMember?: (memberId: string) => void;
    onError?: (error: string | null) => void;
    onRightPanelView?: (view: RightPanelView) => void;
  }): Unsubscribe {
    const unsubscribers: Unsubscribe[] = [];

    if (callbacks.onGameState) {
      unsubscribers.push(this.onGameStateChange(callbacks.onGameState));
    }
    if (callbacks.onProcessing) {
      unsubscribers.push(this.onProcessingChange(callbacks.onProcessing));
    }
    if (callbacks.onSelectedMember) {
      unsubscribers.push(this.onSelectedMemberChange(callbacks.onSelectedMember));
    }
    if (callbacks.onError) {
      unsubscribers.push(this.onErrorChange(callbacks.onError));
    }
    if (callbacks.onRightPanelView) {
      unsubscribers.push(this.onRightPanelViewChange(callbacks.onRightPanelView));
    }

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }

  /**
   * Clear all state (useful for logout or reset)
   */
  reset(): void {
    this.gameState.set(null);
    this.isProcessing.set(false);
    this.selectedMemberId.set('');
    this.error.set(null);
    this.rightPanelView.set('party');
  }
}
