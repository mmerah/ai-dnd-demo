/**
 * ScreenManager
 *
 * Simple hash-based routing system for navigating between screens.
 * No external router library - KISS principle.
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { GameListScreen } from './GameListScreen.js';
import { CharacterSelectionScreen } from './CharacterSelectionScreen.js';
import { ScenarioSelectionScreen } from './ScenarioSelectionScreen.js';
import { GameInterfaceScreen } from './GameInterfaceScreen.js';
import { CatalogBrowserScreen } from './CatalogBrowserScreen.js';

export interface ScreenManagerConfig {
  container: ServiceContainer;
  appContainer: HTMLElement;
}

/**
 * Manages screen navigation and routing
 */
export class ScreenManager {
  private currentScreen: Screen | null = null;
  private config: ScreenManagerConfig;
  private selectedCharacterId: string | null = null;

  constructor(config: ScreenManagerConfig) {
    this.config = config;
    this.setupRouting();
  }

  /**
   * Set up hash change listener for routing
   */
  private setupRouting(): void {
    window.addEventListener('hashchange', () => {
      this.handleRouteChange();
    });
  }

  /**
   * Initialize the screen manager and navigate to initial route
   */
  initialize(): void {
    this.handleRouteChange();
  }

  /**
   * Navigate to a route
   */
  navigateTo(route: string): void {
    window.location.hash = route;
  }

  /**
   * Go back in history
   */
  goBack(): void {
    window.history.back();
  }

  /**
   * Get current route from hash
   */
  getCurrentRoute(): string {
    return window.location.hash.slice(1) || '/';
  }

  /**
   * Handle route changes
   */
  private handleRouteChange(): void {
    const route = this.getCurrentRoute();
    console.log('Route changed to:', route);

    this.unmountCurrentScreen();

    // Parse route and mount appropriate screen
    if (route === '/' || route === '') {
      this.mountGameListScreen();
    } else if (route === '/character-select') {
      this.mountCharacterSelectionScreen();
    } else if (route === '/scenario-select') {
      if (!this.selectedCharacterId) {
        console.warn('No character selected, redirecting to character selection');
        this.navigateTo('/character-select');
        return;
      }
      this.mountScenarioSelectionScreen();
    } else if (route.startsWith('/game/')) {
      const pathAfterGame = route.split('/game/')[1];
      if (!pathAfterGame) {
        console.error('Invalid game route, redirecting to game list');
        this.navigateTo('/');
        return;
      }

      const [gameId, ...rest] = pathAfterGame.split('/');

      if (gameId && rest[0] === 'catalog') {
        this.mountCatalogBrowserScreen(gameId);
      } else if (gameId) {
        this.mountGameInterfaceScreen(gameId);
      } else {
        console.error('Invalid game route, redirecting to game list');
        this.navigateTo('/');
      }
    } else {
      console.warn('Unknown route:', route, '- redirecting to game list');
      this.navigateTo('/');
    }
  }

  /**
   * Unmount current screen
   */
  private unmountCurrentScreen(): void {
    if (this.currentScreen) {
      this.currentScreen.unmount();
      this.currentScreen = null;
    }
    this.config.appContainer.innerHTML = '';
  }

  /**
   * Mount game list screen
   */
  private mountGameListScreen(): void {
    const screen = new GameListScreen({
      container: this.config.container,
      onNewGame: () => {
        this.selectedCharacterId = null;
        this.navigateTo('/character-select');
      },
      onLoadGame: (gameId) => {
        this.navigateTo(`/game/${gameId}`);
      },
    });

    screen.mount(this.config.appContainer);
    this.currentScreen = screen;
  }

  /**
   * Mount character selection screen
   */
  private mountCharacterSelectionScreen(): void {
    const screen = new CharacterSelectionScreen({
      container: this.config.container,
      onBack: () => {
        this.selectedCharacterId = null;
        this.navigateTo('/');
      },
      onNext: (characterId) => {
        this.selectedCharacterId = characterId;
        this.navigateTo('/scenario-select');
      },
    });

    screen.mount(this.config.appContainer);
    this.currentScreen = screen;
  }

  /**
   * Mount scenario selection screen
   */
  private mountScenarioSelectionScreen(): void {
    if (!this.selectedCharacterId) {
      console.error('No character selected');
      this.navigateTo('/character-select');
      return;
    }

    const screen = new ScenarioSelectionScreen({
      container: this.config.container,
      characterId: this.selectedCharacterId,
      onBack: () => {
        this.navigateTo('/character-select');
      },
      onStartGame: async (characterId, scenarioId) => {
        await this.createAndStartGame(characterId, scenarioId);
      },
    });

    screen.mount(this.config.appContainer);
    this.currentScreen = screen;
  }

  /**
   * Mount game interface screen
   */
  private mountGameInterfaceScreen(gameId: string): void {
    const screen = new GameInterfaceScreen({
      container: this.config.container,
      gameId,
    });

    screen.mount(this.config.appContainer);
    this.currentScreen = screen;
  }

  /**
   * Mount catalog browser screen
   */
  private mountCatalogBrowserScreen(gameId: string): void {
    const screen = new CatalogBrowserScreen({
      container: this.config.container,
      onBack: () => {
        this.navigateTo(`/game/${gameId}`);
      },
    });

    screen.mount(this.config.appContainer);
    this.currentScreen = screen;
  }

  /**
   * Create a new game and navigate to it
   */
  private async createAndStartGame(characterId: string, scenarioId: string): Promise<void> {
    const { container } = this.config;

    try {
      const response = await container.gameApiService.createGame(scenarioId, characterId);
      console.log('Game created:', response.game_id);

      // Navigate to the new game
      this.navigateTo(`/game/${response.game_id}`);
    } catch (error) {
      console.error('Failed to create game:', error);
      const message = error instanceof Error ? error.message : 'Failed to create game';
      alert(`Error: ${message}`);
      throw error;
    }
  }

  /**
   * Clean up
   */
  destroy(): void {
    this.unmountCurrentScreen();
    window.removeEventListener('hashchange', () => this.handleRouteChange());
  }
}
