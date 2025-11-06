/**
 * GameListScreen
 *
 * Screen for browsing and loading saved games, or starting a new game.
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { div, button } from '../utils/dom.js';
import { GameListItem } from '../components/game/GameListItem.js';

export interface GameListScreenProps {
  container: ServiceContainer;
  onNewGame: () => void;
  onLoadGame: (gameId: string) => void;
}

/**
 * Game list screen with saved games and new game option
 */
export class GameListScreen extends Screen {
  private gamesContainer: HTMLElement | null = null;
  private loadingIndicator: HTMLElement | null = null;
  private errorDisplay: HTMLElement | null = null;
  private emptyState: HTMLElement | null = null;
  private gameItems: GameListItem[] = [];

  constructor(private props: GameListScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const screen = div({ class: 'game-list-screen' });

    // Header
    const header = div({ class: 'game-list-screen__header' });
    const title = div({ class: 'game-list-screen__title' }, 'Saved Games');
    const newGameButton = button('New Game', {
      class: 'game-list-screen__new-game-btn',
      onclick: () => this.props.onNewGame(),
    });
    header.appendChild(title);
    header.appendChild(newGameButton);

    // Content container
    const content = div({ class: 'game-list-screen__content' });

    // Loading indicator
    this.loadingIndicator = div({ class: 'game-list-screen__loading' }, 'Loading saved games...');

    // Error display
    this.errorDisplay = div({ class: 'game-list-screen__error' });
    this.errorDisplay.style.display = 'none';

    // Empty state
    this.emptyState = div(
      { class: 'game-list-screen__empty' },
      'No saved games found. Click "New Game" to start your adventure!'
    );
    this.emptyState.style.display = 'none';

    // Games container
    this.gamesContainer = div({ class: 'game-list-screen__games' });

    content.appendChild(this.loadingIndicator);
    content.appendChild(this.errorDisplay);
    content.appendChild(this.emptyState);
    content.appendChild(this.gamesContainer);

    screen.appendChild(header);
    screen.appendChild(content);

    return screen;
  }

  override onMount(): void {
    this.loadGames();
  }

  override onUnmount(): void {
    // Clean up game items
    this.gameItems.forEach((item) => item.unmount());
    this.gameItems = [];
  }

  private async loadGames(): Promise<void> {
    const { container } = this.props;

    try {
      this.showLoading();

      const games = await container.gameApiService.listGames();

      if (games.length === 0) {
        this.showEmpty();
      } else {
        // Map GameState to the expected format
        const gameList = games.map(game => ({
          game_id: game.game_id,
          scenario_name: game.scenario_title,
          character_name: game.character.sheet.name,
          last_saved: game.last_saved ?? game.created_at ?? '',
          created_at: game.created_at ?? '',
        }));
        this.showGames(gameList);
      }
    } catch (error) {
      console.error('Failed to load games:', error);
      const message = error instanceof Error ? error.message : 'Failed to load saved games';
      this.showError(message);
    }
  }

  private showLoading(): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.emptyState || !this.gamesContainer)
      return;

    this.loadingIndicator.style.display = 'block';
    this.errorDisplay.style.display = 'none';
    this.emptyState.style.display = 'none';
    this.gamesContainer.innerHTML = '';
  }

  private showError(message: string): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.emptyState) return;

    this.loadingIndicator.style.display = 'none';
    this.emptyState.style.display = 'none';
    this.errorDisplay.style.display = 'block';
    this.errorDisplay.innerHTML = `
      <div class="game-list-screen__error-title">Failed to Load Games</div>
      <div class="game-list-screen__error-message">${message}</div>
      <button class="game-list-screen__retry-btn">Retry</button>
    `;

    const retryBtn = this.errorDisplay.querySelector('.game-list-screen__retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.loadGames());
    }
  }

  private showEmpty(): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.emptyState || !this.gamesContainer)
      return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'none';
    this.emptyState.style.display = 'block';
    this.gamesContainer.innerHTML = '';
  }

  private showGames(
    games: Array<{
      game_id: string;
      scenario_name: string;
      character_name: string;
      last_saved: string;
      created_at: string;
    }>
  ): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.emptyState || !this.gamesContainer)
      return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'none';
    this.emptyState.style.display = 'none';
    this.gamesContainer.innerHTML = '';

    // Clear existing game items
    this.gameItems.forEach((item) => item.unmount());
    this.gameItems = [];

    // Create and mount game items
    games.forEach((game) => {
      if (!this.gamesContainer) return;

      const gameItem = new GameListItem({
        gameId: game.game_id,
        scenarioName: game.scenario_name,
        characterName: game.character_name,
        lastSaved: game.last_saved,
        createdAt: game.created_at,
        onLoad: (gameId) => this.handleLoadGame(gameId),
        onDelete: (gameId) => this.handleDeleteGame(gameId),
      });

      gameItem.mount(this.gamesContainer);
      this.gameItems.push(gameItem);
    });
  }

  private handleLoadGame(gameId: string): void {
    this.props.onLoadGame(gameId);
  }

  private async handleDeleteGame(gameId: string): Promise<void> {
    const { container } = this.props;

    try {
      await container.gameApiService.deleteGame(gameId);
      // Reload games after successful deletion
      await this.loadGames();
    } catch (error) {
      console.error('Failed to delete game:', error);
      const message = error instanceof Error ? error.message : 'Failed to delete game';
      alert(`Error: ${message}`);
    }
  }
}
