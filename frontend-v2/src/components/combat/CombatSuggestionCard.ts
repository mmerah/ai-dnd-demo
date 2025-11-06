/**
 * CombatSuggestionCard component
 *
 * Displays combat suggestions from allied NPCs during their turn.
 * Shows suggested action with options to accept or override.
 */

import { Component } from '../base/Component.js';
import { createElement } from '../../utils/dom.js';
import type { CombatSuggestion } from '../../types/generated/CombatSuggestion.js';

export interface CombatSuggestionCardProps {
  onAccept: (suggestion: CombatSuggestion) => Promise<void>;
  onOverride: (suggestion: CombatSuggestion) => void;
}

export class CombatSuggestionCard extends Component<CombatSuggestionCardProps> {
  private container: HTMLElement | null = null;
  private titleElement: HTMLElement | null = null;
  private actionTextElement: HTMLElement | null = null;
  private acceptButton: HTMLButtonElement | null = null;
  private overrideButton: HTMLButtonElement | null = null;
  private currentSuggestion: CombatSuggestion | null = null;
  private isProcessing: boolean = false;

  protected render(): HTMLElement {
    this.container = createElement('div', {
      class: 'combat-suggestion-card',
      style: 'display: none;', // Hidden by default
    });

    // Header
    const header = createElement('div', {
      class: 'combat-suggestion-card__header',
    });

    this.titleElement = createElement('h3', {
      class: 'combat-suggestion-card__title',
    });
    this.titleElement.textContent = 'Combat Suggestion';
    header.appendChild(this.titleElement);

    // Action text
    this.actionTextElement = createElement('p', {
      class: 'combat-suggestion-card__action-text',
    });
    this.actionTextElement.textContent = '';

    // Actions container
    const actions = createElement('div', {
      class: 'combat-suggestion-card__actions',
    });

    // Accept button
    this.acceptButton = createElement('button', {
      class: 'combat-suggestion-card__button combat-suggestion-card__button--accept',
    }) as HTMLButtonElement;
    this.acceptButton.textContent = 'Use This Action';
    this.acceptButton.addEventListener('click', () => this.handleAccept());

    // Override button
    this.overrideButton = createElement('button', {
      class: 'combat-suggestion-card__button combat-suggestion-card__button--override',
    }) as HTMLButtonElement;
    this.overrideButton.textContent = 'Do Something Else';
    this.overrideButton.addEventListener('click', () => this.handleOverride());

    actions.appendChild(this.acceptButton);
    actions.appendChild(this.overrideButton);

    // Assemble
    this.container.appendChild(header);
    this.container.appendChild(this.actionTextElement);
    this.container.appendChild(actions);

    return this.container;
  }

  /**
   * Show suggestion card with NPC action
   */
  public showSuggestion(suggestion: CombatSuggestion): void {
    if (!this.container || !this.titleElement || !this.actionTextElement) {
      console.error('[CombatSuggestionCard] Card elements not initialized');
      return;
    }

    // Validate required fields (fail-fast)
    if (!suggestion.npc_id || !suggestion.npc_name || !suggestion.action_text) {
      console.error(
        '[CombatSuggestionCard] Invalid suggestion - missing required fields:',
        suggestion
      );
      return;
    }

    this.currentSuggestion = suggestion;
    this.isProcessing = false;

    // Update content
    this.titleElement.textContent = `${suggestion.npc_name}'s Turn`;
    this.actionTextElement.textContent = suggestion.action_text;

    // Show card
    this.container.style.display = 'block';

    console.log('[CombatSuggestionCard] Displayed suggestion:', suggestion);
  }

  /**
   * Hide suggestion card
   */
  public hideSuggestion(): void {
    if (this.container) {
      this.container.style.display = 'none';
    }
    this.currentSuggestion = null;
    this.isProcessing = false;

    // Re-enable buttons
    if (this.acceptButton) this.acceptButton.disabled = false;
    if (this.overrideButton) this.overrideButton.disabled = false;
  }

  /**
   * Handle accept button click
   */
  private async handleAccept(): Promise<void> {
    if (!this.currentSuggestion) {
      console.warn('[CombatSuggestionCard] No suggestion to accept');
      return;
    }

    if (this.isProcessing) {
      console.warn('[CombatSuggestionCard] Already processing a suggestion');
      return;
    }

    this.isProcessing = true;

    // Disable buttons during processing
    if (this.acceptButton) this.acceptButton.disabled = true;
    if (this.overrideButton) this.overrideButton.disabled = true;

    try {
      await this.props.onAccept(this.currentSuggestion);
      // Hide after successful acceptance
      this.hideSuggestion();
    } catch (error) {
      console.error('[CombatSuggestionCard] Failed to accept suggestion:', error);
      // Re-enable buttons on error to allow retry
      this.isProcessing = false;
      if (this.acceptButton) this.acceptButton.disabled = false;
      if (this.overrideButton) this.overrideButton.disabled = false;
    }
  }

  /**
   * Handle override button click
   */
  private handleOverride(): void {
    if (!this.currentSuggestion) {
      console.warn('[CombatSuggestionCard] No suggestion to override');
      return;
    }

    const suggestion = this.currentSuggestion;
    this.props.onOverride(suggestion);

    // Hide the card
    this.hideSuggestion();
  }
}
