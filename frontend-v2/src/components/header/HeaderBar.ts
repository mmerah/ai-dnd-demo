/**
 * HeaderBar Component
 *
 * Displays game context information and actions:
 * - Exit/Leave game button
 * - Current location + danger level
 * - Game time (Day X, HH:MM)
 * - Combat indicator
 * - Active agent indicator
 * - Save game button
 */

import { Component } from '../base/Component.js';
import { createElement, div, span } from '../../utils/dom.js';
import { Modal } from '../common/Modal.js';
import type { StateStore } from '../../services/state/StateStore.js';
import type { GameState } from '../../types/generated/GameState.js';
import type { DangerLevel } from '../../types/generated/GameState.js';

export interface HeaderBarProps {
  stateStore: StateStore;
  onExitGame: () => void;
  onSaveGame: () => void;
  onOpenCatalogs?: () => void;
}

export class HeaderBar extends Component<HeaderBarProps> {
  private locationSpan: HTMLSpanElement | null = null;
  private dangerLevelSpan: HTMLSpanElement | null = null;
  private gameTimeSpan: HTMLSpanElement | null = null;
  private combatIndicator: HTMLSpanElement | null = null;
  private agentIndicator: HTMLSpanElement | null = null;
  private saveButton: HTMLButtonElement | null = null;

  constructor(props: HeaderBarProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'header-bar' });

    // Left side: Location, Time, Combat, Agent info
    const leftSection = div({ class: 'header-bar__left' });

    // Location with danger level
    const locationContainer = span({ class: 'header-bar__location' });
    locationContainer.appendChild(document.createTextNode('📍 '));
    this.locationSpan = span({ class: 'header-bar__location-name' }) as HTMLSpanElement;
    this.locationSpan.textContent = 'Unknown';
    locationContainer.appendChild(this.locationSpan);

    this.dangerLevelSpan = span({ class: 'header-bar__danger-level' }) as HTMLSpanElement;
    locationContainer.appendChild(this.dangerLevelSpan);

    // Game time
    const timeContainer = span({ class: 'header-bar__time' });
    timeContainer.appendChild(document.createTextNode('🕐 '));
    this.gameTimeSpan = span({ class: 'header-bar__time-value' }) as HTMLSpanElement;
    this.gameTimeSpan.textContent = 'Day 1, 00:00';
    timeContainer.appendChild(this.gameTimeSpan);

    // Combat indicator (hidden by default)
    this.combatIndicator = span({ class: 'header-bar__combat-indicator header-bar__combat-indicator--hidden' }) as HTMLSpanElement;
    this.combatIndicator.textContent = '⚔️ COMBAT';

    // Agent indicator
    this.agentIndicator = span({ class: 'header-bar__agent-indicator' }) as HTMLSpanElement;
    this.agentIndicator.appendChild(document.createTextNode('🤖 '));
    const agentName = span({ class: 'header-bar__agent-name' }) as HTMLSpanElement;
    agentName.textContent = 'Narrative';
    this.agentIndicator.appendChild(agentName);

    leftSection.appendChild(locationContainer);
    leftSection.appendChild(timeContainer);
    leftSection.appendChild(this.combatIndicator);
    leftSection.appendChild(this.agentIndicator);

    // Right side: Action buttons
    const rightSection = div({ class: 'header-bar__right' });

    // Catalogs button (if handler provided)
    if (this.props.onOpenCatalogs) {
      const catalogsButton = createElement('button', { class: 'btn btn--small' }) as HTMLButtonElement;
      catalogsButton.textContent = '📚 Catalogs';
      catalogsButton.addEventListener('click', () => {
        if (this.props.onOpenCatalogs) {
          this.props.onOpenCatalogs();
        }
      });
      rightSection.appendChild(catalogsButton);
    }

    // Save button
    this.saveButton = createElement('button', { class: 'btn btn--small' }) as HTMLButtonElement;
    this.saveButton.textContent = '💾 Save';
    this.saveButton.addEventListener('click', () => this.handleSaveClick());

    // Exit button
    const exitButton = createElement('button', { class: 'btn btn--small btn--danger' }) as HTMLButtonElement;
    exitButton.textContent = '🚪 Exit Game';
    exitButton.addEventListener('click', () => this.handleExitClick());

    rightSection.appendChild(this.saveButton);
    rightSection.appendChild(exitButton);

    container.appendChild(leftSection);
    container.appendChild(rightSection);

    return container;
  }

  override onMount(): void {
    // Subscribe to game state changes using Component's subscribe helper
    this.subscribe(this.props.stateStore.gameState$, (gameState) => {
      if (gameState) {
        this.updateFromGameState(gameState);
      }
    });

    // Subscribe to processing state for loading animation on agent indicator
    this.subscribe(this.props.stateStore.isProcessing$, (isProcessing) => {
      this.updateProcessingState(isProcessing);
    });

    // Initial update
    const gameState = this.props.stateStore.getGameState();
    if (gameState) {
      this.updateFromGameState(gameState);
    }
  }

  private updateFromGameState(gameState: GameState): void {
    this.updateLocation(gameState);
    this.updateGameTime(gameState);
    this.updateCombatIndicator(gameState);
    this.updateAgentIndicator(gameState);
  }

  private updateLocation(gameState: GameState): void {
    if (!this.locationSpan || !this.dangerLevelSpan) {
      return;
    }

    // Update location name
    this.locationSpan.textContent = gameState.location || 'Unknown';

    // Update danger level indicator
    const currentLocationId = gameState.scenario_instance?.current_location_id;
    const locationStates = gameState.scenario_instance?.location_states;

    let dangerLevel: DangerLevel | undefined;
    if (currentLocationId && locationStates && locationStates[currentLocationId]) {
      dangerLevel = locationStates[currentLocationId].danger_level;
    }

    // Clear previous classes
    this.dangerLevelSpan.className = 'header-bar__danger-level';

    if (dangerLevel) {
      const dangerInfo = this.getDangerLevelInfo(dangerLevel);
      this.dangerLevelSpan.textContent = ` ${dangerInfo.icon}`;
      this.dangerLevelSpan.classList.add(`header-bar__danger-level--${dangerLevel}`);
      this.dangerLevelSpan.title = dangerInfo.text;
    } else {
      this.dangerLevelSpan.textContent = '';
    }
  }

  private getDangerLevelInfo(level: DangerLevel): { icon: string; text: string } {
    switch (level) {
      case 'safe':
        return { icon: '🛡️', text: 'Safe' };
      case 'low':
        return { icon: '⚠️', text: 'Low Danger' };
      case 'moderate':
        return { icon: '⚠️', text: 'Moderate Danger' };
      case 'high':
        return { icon: '⚠️', text: 'High Danger' };
      case 'extreme':
        return { icon: '☠️', text: 'EXTREME DANGER' };
      case 'cleared':
        return { icon: '✅', text: 'Cleared' };
      default:
        return { icon: '', text: '' };
    }
  }

  private updateGameTime(gameState: GameState): void {
    if (!this.gameTimeSpan) {
      return;
    }

    const gameTime = gameState.game_time;
    if (gameTime && gameTime.day !== undefined && gameTime.hour !== undefined && gameTime.minute !== undefined) {
      const hourStr = String(gameTime.hour).padStart(2, '0');
      const minuteStr = String(gameTime.minute).padStart(2, '0');
      this.gameTimeSpan.textContent = `Day ${gameTime.day}, ${hourStr}:${minuteStr}`;
    } else {
      this.gameTimeSpan.textContent = 'Day 1, 00:00';
    }
  }

  private updateCombatIndicator(gameState: GameState): void {
    if (!this.combatIndicator) {
      return;
    }

    const isInCombat = gameState.combat?.is_active === true;

    if (isInCombat) {
      this.combatIndicator.classList.remove('header-bar__combat-indicator--hidden');
    } else {
      this.combatIndicator.classList.add('header-bar__combat-indicator--hidden');
    }
  }

  private updateAgentIndicator(gameState: GameState): void {
    if (!this.agentIndicator) {
      return;
    }

    const agentType = gameState.active_agent || 'narrative';
    const agentNameSpan = this.agentIndicator.querySelector('.header-bar__agent-name') as HTMLSpanElement;

    if (agentNameSpan) {
      // Capitalize first letter
      agentNameSpan.textContent = agentType.charAt(0).toUpperCase() + agentType.slice(1);
    }
  }

  /**
   * Update agent indicator with loading animation during processing
   * Matches old frontend behavior: adds 'agent-loading' class for pulse effect
   */
  private updateProcessingState(isProcessing: boolean): void {
    if (!this.agentIndicator) {
      return;
    }

    if (isProcessing) {
      this.agentIndicator.classList.add('agent-loading');
    } else {
      this.agentIndicator.classList.remove('agent-loading');
    }
  }

  /**
   * Show auto-save indicator temporarily
   * Matches old frontend behavior: Shows "💾 Auto-saved" for 2 seconds
   */
  public showAutoSaveIndicator(): void {
    if (!this.saveButton) {
      return;
    }

    const originalText = this.saveButton.textContent;
    this.saveButton.textContent = '💾 Auto-saved';

    setTimeout(() => {
      if (this.saveButton) {
        this.saveButton.textContent = originalText;
      }
    }, 2000);
  }

  private handleSaveClick(): void {
    this.props.onSaveGame();
  }

  private async handleExitClick(): Promise<void> {
    const confirmed = await Modal.confirm(
      'Are you sure you want to exit the game? Make sure you have saved your progress.',
      'Exit Game'
    );

    if (confirmed) {
      this.props.onExitGame();
    }
  }
}
