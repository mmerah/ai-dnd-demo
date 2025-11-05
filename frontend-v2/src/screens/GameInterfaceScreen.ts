/**
 * GameInterfaceScreen
 *
 * Main game interface with 3-panel layout:
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

export interface GameInterfaceScreenProps {
  container: ServiceContainer;
  gameId: string;
}

export class GameInterfaceScreen extends Screen {
  private chatPanel: ChatPanel | null = null;
  private partyPanel: PartyPanel | null = null;
  private locationPanel: LocationPanel | null = null;

  constructor(private props: GameInterfaceScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const { container } = this.props;

    // Main container with 3-panel layout
    const screen = div({ class: 'game-interface-screen' });

    // Left panel (25%)
    const leftPanel = div({ class: 'panel panel--left' });
    this.locationPanel = new LocationPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.locationPanel);
    this.locationPanel.mount(leftPanel);

    // Center panel (50%)
    const centerPanel = div({ class: 'panel panel--center' });
    this.chatPanel = new ChatPanel({
      stateStore: container.stateStore,
      onSendMessage: (message) => this.handleSendMessage(message),
    });
    this.registerComponent(this.chatPanel);
    this.chatPanel.mount(centerPanel);

    // Right panel (25%)
    const rightPanel = div({ class: 'panel panel--right' });
    this.partyPanel = new PartyPanel({
      stateStore: container.stateStore,
    });
    this.registerComponent(this.partyPanel);
    this.partyPanel.mount(rightPanel);

    screen.appendChild(leftPanel);
    screen.appendChild(centerPanel);
    screen.appendChild(rightPanel);

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

    container.sseService.onError((error) => {
      console.error('SSE error:', error);
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
}
