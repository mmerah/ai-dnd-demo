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
import type { ContentPackSummary } from '../types/generated/ContentPackSummary.js';

export interface ScenarioSelectionScreenProps {
  container: ServiceContainer;
  characterId: string;
  onBack: () => void;
  onStartGame: (characterId: string, scenarioId: string, contentPacks?: string[]) => void;
}

/**
 * Scenario selection screen
 */
export class ScenarioSelectionScreen extends Screen {
  private scenariosContainer: HTMLElement | null = null;
  private loadingIndicator: HTMLElement | null = null;
  private errorDisplay: HTMLElement | null = null;
  private startGameButton: HTMLButtonElement | null = null;
  private contentPackContainer: HTMLElement | null = null;
  private scenarioCards: ScenarioCard[] = [];
  private selectedScenarioId: string | null = null;
  private scenarios: ScenarioSheet[] = [];
  private contentPacks: ContentPackSummary[] = [];
  private selectedContentPacks: string[] = [];
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

    // Content pack section (hidden initially, shown after scenario selected)
    this.contentPackContainer = div({ class: 'scenario-selection-screen__content-packs' });
    this.contentPackContainer.style.display = 'none';

    const contentPackTitle = div(
      { class: 'scenario-selection-screen__section-title' },
      'Additional Content (Optional)'
    );
    this.contentPackContainer.appendChild(contentPackTitle);

    const contentPackList = div({ class: 'scenario-selection-screen__pack-list' });
    this.contentPackContainer.appendChild(contentPackList);

    content.appendChild(this.loadingIndicator);
    content.appendChild(this.errorDisplay);
    content.appendChild(this.scenariosContainer);
    content.appendChild(this.contentPackContainer);

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
    this.loadContentPacks();
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

  /**
   * Load available content packs
   */
  private async loadContentPacks(): Promise<void> {
    const { container } = this.props;

    try {
      const response = await container.catalogApiService.getContentPacks();
      this.contentPacks = response.packs || [];

      console.log(`[ContentPacks] Loaded ${this.contentPacks.length} content packs`);

      // Filter out SRD (it's always included by default)
      const additionalPacks = this.contentPacks.filter((pack) => pack.id !== 'srd');

      if (additionalPacks.length > 0) {
        this.renderContentPacks(additionalPacks);
      } else {
        // Show informational message when no additional packs available
        this.renderNoContentPacks();
      }
    } catch (error) {
      console.warn('[ContentPacks] Failed to load content packs:', error);
      // Content packs are optional, so we don't show an error to the user
      this.renderNoContentPacks();
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

    // Auto-select first scenario (matches old frontend behavior)
    if (scenarios.length > 0 && !this.selectedScenarioId) {
      const firstScenario = scenarios[0];
      if (firstScenario?.id) {
        this.handleSelectScenario(firstScenario.id);
        console.log('[UI] Auto-selected first scenario:', firstScenario.title);
      }
    }
  }

  /**
   * Render content pack checkboxes
   */
  private renderContentPacks(packs: ContentPackSummary[]): void {
    if (!this.contentPackContainer) return;

    const packList = this.contentPackContainer.querySelector('.scenario-selection-screen__pack-list');
    if (!packList) return;

    packList.innerHTML = '';

    packs.forEach((pack) => {
      const packItem = div({ class: 'scenario-selection-screen__pack-item' });

      const label = document.createElement('label');
      label.className = 'scenario-selection-screen__pack-label';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = pack.id;
      checkbox.className = 'scenario-selection-screen__pack-checkbox';

      checkbox.addEventListener('change', (e) => {
        const target = e.target as HTMLInputElement;
        if (target.checked) {
          if (!this.selectedContentPacks.includes(pack.id)) {
            this.selectedContentPacks.push(pack.id);
          }
        } else {
          this.selectedContentPacks = this.selectedContentPacks.filter((id) => id !== pack.id);
        }
        console.log('[ContentPacks] Selected packs:', this.selectedContentPacks);
      });

      const packInfo = div({ class: 'scenario-selection-screen__pack-info' });
      packInfo.innerHTML = `
        <strong>${pack.name}</strong> v${pack.version}<br>
        <small style="color: var(--text-secondary);">${pack.description}</small><br>
        <small style="color: var(--text-tertiary);">by ${pack.author}</small>
      `;

      label.appendChild(checkbox);
      label.appendChild(packInfo);
      packItem.appendChild(label);
      packList.appendChild(packItem);
    });
  }

  /**
   * Render informational message when no additional content packs available
   */
  private renderNoContentPacks(): void {
    if (!this.contentPackContainer) return;

    const packList = this.contentPackContainer.querySelector('.scenario-selection-screen__pack-list');
    if (!packList) return;

    packList.innerHTML = `
      <div style="color: var(--text-secondary); padding: 1rem; text-align: center;">
        <p>No additional content packs available.</p>
        <small>The base SRD content is always included.</small>
      </div>
    `;
  }

  private handleSelectScenario(scenarioId: string): void {
    this.selectedScenarioId = scenarioId;

    // Update all cards to reflect selection
    this.scenarioCards.forEach((card) => {
      const cardProps = card as unknown as { props: ScenarioCardProps };
      const isSelected = cardProps.props.scenario.id === scenarioId;
      card.update({ isSelected });
    });

    // Show content pack section after scenario selected (matches old frontend behavior)
    if (this.contentPackContainer) {
      this.contentPackContainer.style.display = 'block';
    }

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
      // Pass selected content packs (if any) to create game
      this.props.onStartGame(
        this.props.characterId,
        this.selectedScenarioId,
        this.selectedContentPacks.length > 0 ? this.selectedContentPacks : undefined
      );
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
