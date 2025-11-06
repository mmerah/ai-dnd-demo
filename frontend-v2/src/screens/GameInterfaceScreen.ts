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
      onReloadGameState: () => this.loadGameState(this.props.gameId),
    });
    this.registerComponent(this.chroniclePanel);
    this.chroniclePanel.mount(leftPanel);

    // Center panel (50%)
    const centerPanel = div({ class: 'panel panel--center' });

    // Combat suggestion card (shows/hides based on suggestions)
    this.combatSuggestionCard = new CombatSuggestionCard({
      onAccept: (suggestion) => this.handleAcceptSuggestion(suggestion),
      onOverride: (suggestion) => this.handleOverrideSuggestion(suggestion),
    });
    this.registerComponent(this.combatSuggestionCard);
    this.combatSuggestionCard.mount(centerPanel);

    // Chat panel
    this.chatPanel = new ChatPanel({
      stateStore: container.stateStore,
      onSendMessage: (message) => this.handleSendMessage(message),
    });
    this.registerComponent(this.chatPanel);
    this.chatPanel.mount(centerPanel);

    // Right panel (25%)
    this.rightPanelContainer = div({ class: 'panel panel--right' });

    // Create all right panel views
    this.partyPanel = new PartyPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.partyPanel);

    this.characterSheetPanel = new CharacterSheetPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.characterSheetPanel);

    this.inventoryPanel = new InventoryPanel({
      stateStore: container.stateStore,
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

    // Load game state
    this.loadGameState(gameId);

    // Connect to SSE
    container.sseService.connect(gameId);

    // Subscribe to SSE events
    container.sseService.on('game_update', (event) => {
      console.log('Game update received:', event);
      // Reload game state when updated
      this.loadGameState(gameId);
    });

    container.sseService.on('narrative_chunk', (event) => {
      console.log('Narrative chunk:', event);
      // Handle streaming narrative
    });

    container.sseService.on('combat_suggestion', (event) => {
      console.log('Combat suggestion received:', event);
      if (event.type === 'combat_suggestion' && this.combatSuggestionCard) {
        this.combatSuggestionCard.showSuggestion(event.data.suggestion);
      }
    });

    container.sseService.onError((error) => {
      console.error('SSE error:', error);
      container.stateStore.setError(error.message);
    });

    // Subscribe to right panel view changes
    container.stateStore.onRightPanelViewChange((view) => {
      this.switchRightPanel(view);
    });

    // Initial panel render
    this.switchRightPanel(container.stateStore.getRightPanelView());
  }

  override onUnmount(): void {
    const { container } = this.props;

    // Disconnect SSE
    container.sseService.disconnect();

    // Clear state
    container.stateStore.reset();
  }

  private async loadGameState(gameId: string): Promise<void> {
    const { container } = this.props;

    try {
      container.stateStore.setIsProcessing(true);
      const gameState = await container.gameApiService.getGameState(gameId);
      container.stateStore.setGameState(gameState);
    } catch (error) {
      console.error('Failed to load game state:', error);
      const message = error instanceof Error ? error.message : 'Failed to load game';
      container.stateStore.setError(message);
    } finally {
      container.stateStore.setIsProcessing(false);
    }
  }

  private async handleSendMessage(message: string): Promise<void> {
    const { container, gameId } = this.props;

    try {
      container.stateStore.setIsProcessing(true);
      container.stateStore.clearError();

      await container.gameApiService.sendAction(gameId, message);

      // State will be updated via SSE
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      container.stateStore.setError(errorMessage);
      container.stateStore.setIsProcessing(false);
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
      throw error; // Re-throw so the card can handle retry
    }
  }

  private handleOverrideSuggestion(suggestion: CombatSuggestion): void {
    console.log('[GameInterfaceScreen] Overriding combat suggestion for:', suggestion.npc_name);

    // Add system message
    const message = `Controlling ${suggestion.npc_name} manually. Type your action in the chat.`;

    // Show in UI (we'll use error state temporarily for user feedback)
    this.props.container.stateStore.setError(message);
    setTimeout(() => {
      const currentError = this.props.container.stateStore.getError();
      if (currentError === message) {
        this.props.container.stateStore.clearError();
      }
    }, 5000);

    // Focus the chat input
    if (this.chatPanel) {
      // The ChatPanel should expose a method to focus its input
      // For now, we can use DOM manipulation as a fallback
      const chatInput = document.querySelector<HTMLTextAreaElement>('.chat-input__textarea');
      if (chatInput) {
        chatInput.focus();
      }
    }
  }
}
