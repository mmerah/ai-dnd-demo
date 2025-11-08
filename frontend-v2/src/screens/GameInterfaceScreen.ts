/**
 * GameInterfaceScreen
 *
 * Main game interface with header bar and 3-panel layout:
 * - Header bar: Location, time, combat status, agent, actions
 * - Left panel (25%): Location and Chronicle
 * - Center panel (50%): Chat
 * - Right panel (25%): Party and Combat
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { div } from '../utils/dom.js';
import { ChatPanel } from '../components/chat/ChatPanel.js';
import { PartyPanel } from '../components/party/PartyPanel.js';
import { LocationPanel } from '../components/location/LocationPanel.js';
import { CombatPanel } from '../components/combat/CombatPanel.js';
import { CombatSuggestionCard } from '../components/combat/CombatSuggestionCard.js';
import { ChroniclePanel } from '../components/chronicle/ChroniclePanel.js';
import { CharacterSheetPanel } from '../components/character-sheet/CharacterSheetPanel.js';
import { InventoryPanel } from '../components/inventory/InventoryPanel.js';
import { HeaderBar } from '../components/header/HeaderBar.js';
import { Toast } from '../components/common/Toast.js';
import type { RightPanelView } from '../services/state/StateStore.js';
import type { CombatSuggestion } from '../types/generated/CombatSuggestion.js';

export interface GameInterfaceScreenProps {
  container: ServiceContainer;
  gameId: string;
  onExitGame?: () => void;
}

export class GameInterfaceScreen extends Screen {
  private headerBar: HeaderBar | null = null;
  private chatPanel: ChatPanel | null = null;
  private combatSuggestionCard: CombatSuggestionCard | null = null;
  private partyPanel: PartyPanel | null = null;
  private characterSheetPanel: CharacterSheetPanel | null = null;
  private inventoryPanel: InventoryPanel | null = null;
  private locationPanel: LocationPanel | null = null;
  private combatPanel: CombatPanel | null = null;
  private chroniclePanel: ChroniclePanel | null = null;
  private rightPanelContainer: HTMLElement | null = null;
  private currentRightPanel: 'party' | 'character-sheet' | 'inventory' | null = null;

  // Streaming narrative state
  private narrativeBuffer: string = '';
  private narrativeMessageKey: string | null = null;

  constructor(private props: GameInterfaceScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const { container } = this.props;

    // Main container with header + 3-panel layout
    const screen = div({ class: 'game-interface-screen-wrapper' });

    // Header bar
    this.headerBar = new HeaderBar({
      stateStore: container.stateStore,
      onExitGame: () => this.handleExitGame(),
      onSaveGame: () => this.handleSaveGame(),
      onOpenCatalogs: () => this.handleOpenCatalogs(),
    });
    this.registerComponent(this.headerBar);
    this.headerBar.mount(screen);

    // 3-panel game interface
    const gameInterface = div({ class: 'game-interface-screen' });

    // Left panel (25%) - Location and Chronicle
    const leftPanel = div({ class: 'panel panel--left' });

    // Location panel (top of left panel)
    this.locationPanel = new LocationPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.locationPanel);
    this.locationPanel.mount(leftPanel);

    // Combat panel (shows/hides automatically based on combat state)
    this.combatPanel = new CombatPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.combatPanel);
    this.combatPanel.mount(leftPanel);

    // Chronicle panel (bottom of left panel)
    this.chroniclePanel = new ChroniclePanel({
      gameId: this.props.gameId,
      journalApiService: container.journalApiService,
      stateStore: container.stateStore,
      onReloadGameState: () => this.loadGameState(this.props.gameId),
    });
    this.registerComponent(this.chroniclePanel);
    this.chroniclePanel.mount(leftPanel);

    // Center panel (50%)
    const centerPanel = div({ class: 'panel panel--center' });

    // Chat panel
    this.chatPanel = new ChatPanel({
      stateStore: container.stateStore,
      onSendMessage: (message) => this.handleSendMessage(message),
      onRequestAllySuggestion: () => this.handleRequestAllySuggestion(),
    });
    this.registerComponent(this.chatPanel);
    this.chatPanel.mount(centerPanel);

    // Combat suggestion card (shows/hides based on suggestions) - mounted at bottom of chat
    this.combatSuggestionCard = new CombatSuggestionCard({
      onAccept: (suggestion) => this.handleAcceptSuggestion(suggestion),
      onOverride: (suggestion) => this.handleOverrideSuggestion(suggestion),
    });
    this.registerComponent(this.combatSuggestionCard);
    this.chatPanel.mountSuggestionCard(this.combatSuggestionCard);

    // Right panel (25%)
    this.rightPanelContainer = div({ class: 'panel panel--right' });

    // Create all right panel views
    this.partyPanel = new PartyPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.partyPanel);

    this.characterSheetPanel = new CharacterSheetPanel({
      stateStore: container.stateStore,
      gameApiService: container.gameApiService,
    });
    this.registerComponent(this.characterSheetPanel);

    this.inventoryPanel = new InventoryPanel({
      stateStore: container.stateStore,
      gameApi: container.gameApiService,
    });
    this.registerComponent(this.inventoryPanel);

    gameInterface.appendChild(leftPanel);
    gameInterface.appendChild(centerPanel);
    gameInterface.appendChild(this.rightPanelContainer);

    screen.appendChild(gameInterface);

    return screen;
  }

  override onMount(): void {
    const { container, gameId } = this.props;

    // Call resume endpoint for legacy parity (backend is a no-op acknowledgment)
    // This matches the old frontend behavior
    this.resumeGame(gameId);

    // Load game state
    this.loadGameState(gameId);

    // IMPORTANT: Register SSE handlers BEFORE connecting to prevent race condition
    // where early events might arrive before handlers are registered
    this.setupSseEventHandlers(container, gameId);

    // Connect to SSE (now that handlers are registered)
    container.sseService.connect(gameId);

    // Subscribe to right panel view changes
    container.stateStore.onRightPanelViewChange((view) => {
      this.switchRightPanel(view);
    });

    // Initial panel render
    this.switchRightPanel(container.stateStore.getRightPanelView());
  }

  /**
   * Setup handlers for all SSE event types
   */
  private setupSseEventHandlers(container: ServiceContainer, gameId: string): void {
    // Connection confirmation
    container.sseService.on('connected', (event) => {
      console.log('[SSE] Connection established:', event);
    });

    // Initial narrative (opening scene for new games)
    container.sseService.on('initial_narrative', (event) => {
      console.log('[SSE] Initial narrative received');
      if (event.type === 'initial_narrative') {
        // IMPORTANT: Skip adding the narrative if conversation_history was already loaded
        // This prevents duplicating the opening DM message on both new and resumed games
        const gameState = container.stateStore.getGameState();
        const hasConversationHistory = gameState?.conversation_history && gameState.conversation_history.length > 0;

        if (hasConversationHistory) {
          console.log('[SSE] Skipping initial_narrative - conversation history already loaded');
          // Still add the scenario title as a visual separator (optional)
          if (event.data.scenario_title) {
            this.chatPanel?.addRealtimeMessage({
              type: 'system',
              content: `=== ${event.data.scenario_title} ===`,
              timestamp: event.data.timestamp,
            });
          }
          return;
        }

        // For new games without history, add both title and narrative
        if (event.data.scenario_title) {
          this.chatPanel?.addRealtimeMessage({
            type: 'system',
            content: `=== ${event.data.scenario_title} ===`,
            timestamp: event.data.timestamp,
          });
        }
        // Add narrative as DM message (with defensive null check)
        const narrative = event.data.narrative ?? '';
        if (narrative) {
          this.chatPanel?.addRealtimeMessage({
            type: 'assistant',
            content: narrative,
            timestamp: event.data.timestamp,
          });
        }
      }
    });

    // Non-streaming narrative
    container.sseService.on('narrative', (event) => {
      console.log('[SSE] Narrative received');
      if (event.type === 'narrative') {
        // Defensive check: ensure content is not null/undefined
        const content = event.data.content ?? '';
        if (!content) {
          console.warn('[SSE] Narrative event has empty content, skipping');
          return;
        }
        this.chatPanel?.addRealtimeMessage({
          type: 'assistant',
          content: content,
          timestamp: event.data.timestamp,
        });
      }
    });

    // Streaming narrative chunks
    container.sseService.on('narrative_chunk', (event) => {
      console.log('[SSE] Narrative chunk received');
      if (event.type === 'narrative_chunk') {
        const delta = event.data.delta ?? '';

        if (!this.narrativeMessageKey) {
          // Create new message for first chunk
          this.narrativeBuffer = delta;
          this.narrativeMessageKey = this.chatPanel?.addRealtimeMessage({
            type: 'assistant',
            content: delta,
            timestamp: new Date().toISOString(),
          }) ?? null;
        } else {
          // Update existing message with accumulated content
          this.narrativeBuffer += delta;
          if (this.narrativeMessageKey) {
            this.chatPanel?.updateMessage(this.narrativeMessageKey, this.narrativeBuffer);
          }
        }
      }
    });

    // Tool calls
    container.sseService.on('tool_call', (event) => {
      console.log('[SSE] Tool call received:', event);
      if (event.type === 'tool_call') {
        this.chatPanel?.addRealtimeMessage({
          type: 'tool',
          content: event.data.tool_name,
          metadata: {
            toolName: event.data.tool_name,
            parameters: event.data.parameters,
          },
        });
      }
    });

    // Tool results
    container.sseService.on('tool_result', (event) => {
      console.log('[SSE] Tool result received:', event);
      if (event.type === 'tool_result') {
        const result = event.data.result;
        let resultText = '';

        // Format tool result using discriminated union type checking
        // Result is a union of strongly-typed result models from the backend
        if (result && typeof result === 'object') {
          // Type guard function for LevelUpResult
          const isLevelUpResult = (r: unknown): r is { type: string; old_level: number; new_level: number; hp_increase: number } => {
            return typeof r === 'object' && r !== null && 'type' in r && (r as any).type === 'level_up';
          };

          // Type guard function for RollDiceResult
          const isRollDiceResult = (r: unknown): r is { roll_type: string; dice: string; modifier: number; total: number; rolls: number[]; ability?: string | null; skill?: string | null; critical?: boolean | null } => {
            return typeof r === 'object' && r !== null && 'roll_type' in r && 'dice' in r && 'total' in r;
          };

          // Check for level_up result
          if (isLevelUpResult(result)) {
            resultText = `⬆️ Level Up: ${result.old_level} → ${result.new_level} (HP +${result.hp_increase})`;
          }
          // Check for dice roll result
          else if (isRollDiceResult(result)) {
            const rolls = result.rolls ?? [];
            const rollsStr = rolls.length > 0 ? `[${rolls.join(', ')}]` : '';
            const modifier = result.modifier ?? 0;
            const modStr = modifier !== 0 ? (modifier > 0 ? `+${modifier}` : `${modifier}`) : '';
            const rollType = result.roll_type.charAt(0).toUpperCase() + result.roll_type.slice(1);

            resultText = `📊 ${rollType} Roll: ${result.dice}${modStr} = ${result.total}`;
            if (rollsStr) resultText += ` ${rollsStr}`;
            if (result.ability) resultText += ` (${result.ability}${result.skill ? ' - ' + result.skill : ''})`;
            if (result.critical === true) resultText += ' - 🎯 CRITICAL!';
            else if (result.critical === false && rolls.includes(1)) resultText += ' - 💀 CRITICAL FAIL!';
          }
          // Generic object result (fallback for other result types)
          else {
            resultText = `✓ ${event.data.tool_name} completed: ${JSON.stringify(result)}`;
          }
        } else {
          // Primitive result (shouldn't happen with current backend typing)
          resultText = `✓ ${event.data.tool_name} completed: ${String(result)}`;
        }

        this.chatPanel?.addRealtimeMessage({
          type: 'tool-result',
          content: resultText,
          timestamp: event.data.timestamp,
          metadata: {
            toolName: event.data.tool_name,
            result: result,
          },
        });
      }
    });

    // NPC dialogue
    container.sseService.on('npc_dialogue', (event) => {
      console.log('[SSE] NPC dialogue received:', event);
      if (event.type === 'npc_dialogue') {
        // Defensive logging to debug npc_name issue
        console.log('[SSE] NPC dialogue npc_name:', event.data.npc_name);
        this.chatPanel?.addRealtimeMessage({
          type: 'npc',
          content: event.data.content,
          timestamp: event.data.timestamp,
          metadata: {
            npcId: event.data.npc_id,
            npcName: event.data.npc_name,
          },
        });
      }
    });

    // Policy warnings
    container.sseService.on('policy_warning', (event) => {
      console.log('[SSE] Policy warning received:', event);
      if (event.type === 'policy_warning') {
        this.chatPanel?.addRealtimeMessage({
          type: 'policy-warning',
          content: event.data.message,
          timestamp: event.data.timestamp,
          metadata: {
            toolName: event.data.tool_name ?? undefined,
            agentType: event.data.agent_type ?? undefined,
          },
        });
      }
    });

    // Combat suggestions
    container.sseService.on('combat_suggestion', (event) => {
      console.log('[SSE] Combat suggestion received:', event);
      if (event.type === 'combat_suggestion') {
        if (!this.combatSuggestionCard) {
          console.error('[SSE] Combat suggestion card not initialized!');
          return;
        }

        // Access the nested suggestion field (generated type guarantees presence)
        const suggestionData = event.data.suggestion;
        console.log('[SSE] Combat suggestion data:', suggestionData);

        this.combatSuggestionCard.showSuggestion(suggestionData);
      }
    });

    // Scenario info (store for location name resolution)
    container.sseService.on('scenario_info', (event) => {
      console.log('[SSE] Scenario info received:', event);
      // Store scenario data globally for location name lookups
      if (event.type === 'scenario_info') {
        (window as any).currentScenario = event.data.current_scenario;
      }
    });

    // Game state updates
    container.sseService.on('game_update', (event) => {
      console.log('[SSE] Game update received');
      try {
        // Prefer the authoritative state sent over SSE to avoid race conditions
        // and stale snapshots from re-fetching immediately after a write.
        // event.data is strongly typed as GameUpdateData with game_state field
        if (event.type === 'game_update') {
          const gameState = event.data.game_state;
          container.stateStore.setGameState(gameState);
        } else {
          console.warn('[SSE] Unexpected event type in game_update handler');
          this.loadGameState(gameId);
        }
      } catch (err) {
        console.error('[SSE] Failed to apply game_update payload, refetching:', err);
        this.loadGameState(gameId);
      }
    });

    // Combat updates (apply incremental update for immediate UI response)
    container.sseService.on('combat_update', (event) => {
      console.log('[SSE] Combat update:', event);
      try {
        if (event.type === 'combat_update') {
          const current = container.stateStore.getGameState();
          const combat = event.data.combat;
          if (current) {
            // Apply a minimal, immutable update to the combat slice
            const updated = { ...current, combat };
            container.stateStore.setGameState(updated);
          }
        }
      } catch (err) {
        console.error('[SSE] Failed to apply combat_update:', err);
      }
    });

    // Processing complete
    container.sseService.on('complete', () => {
      console.log('[SSE] Processing complete');
      container.stateStore.setIsProcessing(false);

      // Reset streaming narrative state
      this.narrativeBuffer = '';
      this.narrativeMessageKey = null;
    });

    // Errors
    container.sseService.on('error', (event) => {
      console.error('[SSE] Error event:', event);
      if (event.type === 'error') {
        this.chatPanel?.addRealtimeMessage({
          type: 'error',
          content: event.data.error,
        });
        container.stateStore.setIsProcessing(false);

        // Reset streaming narrative state on error
        this.narrativeBuffer = '';
        this.narrativeMessageKey = null;
      }
    });

    // Thinking events (optional - for debugging)
    container.sseService.on('thinking', (event) => {
      console.log('[SSE] Thinking:', event);
    });

    // Connection errors
    container.sseService.onError((error) => {
      console.error('[SSE] Connection error:', error);
      container.stateStore.setError(error.message);
    });
  }

  override onUnmount(): void {
    const { container } = this.props;

    // Disconnect SSE
    container.sseService.disconnect();

    // Clear state
    container.stateStore.reset();
  }

  /**
   * Resume a saved game session
   * This is a simple backend acknowledgment for parity with legacy frontend
   */
  private async resumeGame(gameId: string): Promise<void> {
    const { container } = this.props;

    try {
      await container.gameApiService.resumeGame(gameId);
      console.log(`[GameInterfaceScreen] Game ${gameId} resumed`);
    } catch (error) {
      console.warn('[GameInterfaceScreen] Resume endpoint failed (non-critical):', error);
      // Don't fail the entire load if resume fails - it's just for parity
    }
  }

  private async loadGameState(gameId: string): Promise<void> {
    const { container } = this.props;

    try {
      const gameState = await container.gameApiService.getGameState(gameId);
      container.stateStore.setGameState(gameState);
    } catch (error) {
      console.error('Failed to load game state:', error);
      const message = error instanceof Error ? error.message : 'Failed to load game';
      container.stateStore.setError(message);
      Toast.error(`Failed to load game: ${message}`);
    }
    // Note: Don't touch isProcessing here - it's controlled by SSE events (complete/error)
  }

  private async handleSendMessage(message: string): Promise<void> {
    const { container, gameId } = this.props;

    try {
      // IMPORTANT: Add player message to chat IMMEDIATELY (before sending to backend)
      // This matches old frontend behavior and provides instant feedback
      this.chatPanel?.addRealtimeMessage({
        type: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      });

      container.stateStore.setIsProcessing(true);
      container.stateStore.clearError();

      await container.gameApiService.sendAction(gameId, message);

      // Show auto-save indicator (matches old frontend behavior)
      this.headerBar?.showAutoSaveIndicator();

      // State will be updated via SSE
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      container.stateStore.setError(errorMessage);
      container.stateStore.setIsProcessing(false);
      Toast.error(`Failed to send message: ${errorMessage}. Please try again.`);
    }
  }

  private switchRightPanel(view: RightPanelView): void {
    if (!this.rightPanelContainer) {
      return;
    }

    // Don't switch if already showing this view
    if (this.currentRightPanel === view) {
      return;
    }

    // Unmount the current panel properly
    if (this.currentRightPanel === 'party' && this.partyPanel) {
      this.partyPanel.unmount();
    } else if (this.currentRightPanel === 'character-sheet' && this.characterSheetPanel) {
      this.characterSheetPanel.unmount();
    } else if (this.currentRightPanel === 'inventory' && this.inventoryPanel) {
      this.inventoryPanel.unmount();
    }

    // Clear the container
    this.rightPanelContainer.innerHTML = '';

    // Mount the new panel
    switch (view) {
      case 'party':
        if (this.partyPanel) {
          this.partyPanel.mount(this.rightPanelContainer);
        }
        break;
      case 'character-sheet':
        if (this.characterSheetPanel) {
          this.characterSheetPanel.mount(this.rightPanelContainer);
        }
        break;
      case 'inventory':
        if (this.inventoryPanel) {
          this.inventoryPanel.mount(this.rightPanelContainer);
        }
        break;
    }

    this.currentRightPanel = view;
  }

  private handleExitGame(): void {
    if (this.props.onExitGame) {
      this.props.onExitGame();
    } else {
      // Default: navigate to game list
      window.location.hash = '/';
    }
  }

  private handleOpenCatalogs(): void {
    // Navigate to catalog browser for current game
    window.location.hash = `/game/${this.props.gameId}/catalog`;
  }

  private async handleSaveGame(): Promise<void> {
    const { container } = this.props;

    // The backend auto-saves on every action
    // This just provides user feedback
    container.stateStore.setError('Game is auto-saved after every action');

    // Clear the message after 3 seconds
    setTimeout(() => {
      const currentError = container.stateStore.getError();
      if (currentError === 'Game is auto-saved after every action') {
        container.stateStore.clearError();
      }
    }, 3000);
  }

  private async handleRequestAllySuggestion(): Promise<void> {
    const { container, gameId } = this.props;

    try {
      console.log('[GameInterfaceScreen] Requesting ally suggestion');

      // Set processing state to show loading indicator
      container.stateStore.setIsProcessing(true);

      await container.gameApiService.requestAllySuggestion(gameId);

      // The suggestion will arrive via SSE (combat_suggestion event)
      // Processing state will be cleared when complete event arrives
    } catch (error) {
      console.error('[GameInterfaceScreen] Failed to request ally suggestion:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to request suggestion';
      container.stateStore.setError(errorMessage);
      container.stateStore.setIsProcessing(false);
      Toast.error(`Failed to request ally suggestion: ${errorMessage}`);
    }
  }

  private async handleAcceptSuggestion(suggestion: CombatSuggestion): Promise<void> {
    const { container, gameId } = this.props;

    try {
      console.log('[GameInterfaceScreen] Accepting combat suggestion:', suggestion);

      const response = await container.gameApiService.acceptCombatSuggestion(gameId, {
        suggestion_id: suggestion.suggestion_id,
        npc_id: suggestion.npc_id,
        npc_name: suggestion.npc_name,
        action_text: suggestion.action_text,
      });

      console.log('[GameInterfaceScreen] Suggestion accepted:', response);

      // Add system message to chat (via state store for consistency)
      // The backend will handle the action execution and update game state via SSE
    } catch (error) {
      console.error('[GameInterfaceScreen] Failed to accept suggestion:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to accept suggestion';
      container.stateStore.setError(errorMessage);
      Toast.error(`Failed to execute suggested action: ${errorMessage}`);
      throw error; // Re-throw so the card can handle retry
    }
  }

  private handleOverrideSuggestion(suggestion: CombatSuggestion): void {
    console.log('[GameInterfaceScreen] Overriding combat suggestion for:', suggestion.npc_name);

    // Add system message to chat
    this.chatPanel?.addRealtimeMessage({
      type: 'system',
      content: `Controlling ${suggestion.npc_name} manually. Type your action in the chat.`,
    });

    // Focus the chat input
    this.chatPanel?.focusInput();
  }
}
