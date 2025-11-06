/**
 * ScenarioSelectionScreen
 *
 * Screen for selecting a scenario to start a new game.
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { div, button } from '../utils/dom.js';
import { ScenarioCard, type ScenarioCardProps } from '../components/scenario/ScenarioCard.js';
import type { ScenarioSheet } from '../types/generated/ScenarioSheet.js';

export interface ScenarioSelectionScreenProps {
  container: ServiceContainer;
  characterId: string;
  onBack: () => void;
  onStartGame: (characterId: string, scenarioId: string) => void;
}

/**
 * Scenario selection screen
 */
export class ScenarioSelectionScreen extends Screen {
  private scenariosContainer: HTMLElement | null = null;
  private loadingIndicator: HTMLElement | null = null;
  private errorDisplay: HTMLElement | null = null;
  private startGameButton: HTMLButtonElement | null = null;
  private scenarioCards: ScenarioCard[] = [];
  private selectedScenarioId: string | null = null;
  private scenarios: ScenarioSheet[] = [];
  private isCreatingGame: boolean = false;

  constructor(private props: ScenarioSelectionScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const screen = div({ class: 'scenario-selection-screen' });

    // Header
    const header = div({ class: 'scenario-selection-screen__header' });
    const title = div({ class: 'scenario-selection-screen__title' }, 'Select Your Scenario');
    header.appendChild(title);

    // Content container
    const content = div({ class: 'scenario-selection-screen__content' });

    // Loading indicator
    this.loadingIndicator = div(
      { class: 'scenario-selection-screen__loading' },
      'Loading scenarios...'
    );

    // Error display
    this.errorDisplay = div({ class: 'scenario-selection-screen__error' });
    this.errorDisplay.style.display = 'none';

    // Scenarios container
    this.scenariosContainer = div({ class: 'scenario-selection-screen__scenarios' });

    content.appendChild(this.loadingIndicator);
    content.appendChild(this.errorDisplay);
    content.appendChild(this.scenariosContainer);

    // Navigation footer
    const footer = div({ class: 'scenario-selection-screen__footer' });

    const backButton = button('Back', {
      class: 'scenario-selection-screen__back-btn',
      onclick: () => this.props.onBack(),
    });

    this.startGameButton = button('Start Game', {
      class: 'scenario-selection-screen__start-btn',
      disabled: true,
      onclick: () => this.handleStartGame(),
    }) as HTMLButtonElement;

    footer.appendChild(backButton);
    footer.appendChild(this.startGameButton);

    screen.appendChild(header);
    screen.appendChild(content);
    screen.appendChild(footer);

    return screen;
  }

  override onMount(): void {
    this.loadScenarios();
  }

  override onUnmount(): void {
    // Clean up scenario cards
    this.scenarioCards.forEach((card) => card.unmount());
    this.scenarioCards = [];
  }

  private async loadScenarios(): Promise<void> {
    const { container } = this.props;

    try {
      this.showLoading();

      const scenarios = await container.catalogApiService.getScenarios();
      this.scenarios = scenarios;

      if (this.scenarios.length === 0) {
        this.showError('No scenarios available');
      } else {
        this.showScenarios(this.scenarios);
      }
    } catch (error) {
      console.error('Failed to load scenarios:', error);
      const message = error instanceof Error ? error.message : 'Failed to load scenarios';
      this.showError(message);
    }
  }

  private showLoading(): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.scenariosContainer) return;

    this.loadingIndicator.style.display = 'block';
    this.errorDisplay.style.display = 'none';
    this.scenariosContainer.innerHTML = '';
  }

  private showError(message: string): void {
    if (!this.loadingIndicator || !this.errorDisplay) return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'block';
    this.errorDisplay.innerHTML = `
      <div class="scenario-selection-screen__error-title">Failed to Load Scenarios</div>
      <div class="scenario-selection-screen__error-message">${message}</div>
      <button class="scenario-selection-screen__retry-btn">Retry</button>
    `;

    const retryBtn = this.errorDisplay.querySelector('.scenario-selection-screen__retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.loadScenarios());
    }
  }

  private showScenarios(scenarios: ScenarioSheet[]): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.scenariosContainer) return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'none';
    this.scenariosContainer.innerHTML = '';

    // Clear existing cards
    this.scenarioCards.forEach((card) => card.unmount());
    this.scenarioCards = [];

    // Create and mount scenario cards
    scenarios.forEach((scenario) => {
      if (!this.scenariosContainer) return;

      const card = new ScenarioCard({
        scenario,
        isSelected: this.selectedScenarioId === scenario.id,
        onSelect: (scenarioId) => this.handleSelectScenario(scenarioId),
      });

      card.mount(this.scenariosContainer);
      this.scenarioCards.push(card);
    });
  }

  private handleSelectScenario(scenarioId: string): void {
    this.selectedScenarioId = scenarioId;

    // Update all cards to reflect selection
    this.scenarioCards.forEach((card) => {
      const cardProps = card as unknown as { props: ScenarioCardProps };
      const isSelected = cardProps.props.scenario.id === scenarioId;
      card.update({ isSelected });
    });

    // Enable start game button
    if (this.startGameButton) {
      this.startGameButton.disabled = false;
    }
  }

  private async handleStartGame(): Promise<void> {
    if (!this.selectedScenarioId || this.isCreatingGame) return;

    const selectedScenario = this.scenarios.find((s) => s.id === this.selectedScenarioId);
    if (!selectedScenario) return;

    const confirmed = confirm(
      `Start a new game with this scenario?\n\n${selectedScenario.title}\n\n${selectedScenario.description}`
    );

    if (!confirmed) return;

    this.isCreatingGame = true;

    if (this.startGameButton) {
      this.startGameButton.disabled = true;
      this.startGameButton.textContent = 'Creating Game...';
    }

    try {
      this.props.onStartGame(this.props.characterId, this.selectedScenarioId);
    } catch (error) {
      console.error('Failed to start game:', error);
      const message = error instanceof Error ? error.message : 'Failed to start game';
      alert(`Error: ${message}`);

      this.isCreatingGame = false;
      if (this.startGameButton) {
        this.startGameButton.disabled = false;
        this.startGameButton.textContent = 'Start Game';
      }
    }
  }
}
