/**
 * LoadingIndicator component
 *
 * Displays an animated loading indicator when the AI is thinking.
 * Supports dynamic message updates based on active agent type.
 */

import { Component } from '../base/Component.js';
import { createElement, span } from '../../utils/dom.js';

export interface LoadingIndicatorProps {
  message?: string;
  agentType?: string;
}

export class LoadingIndicator extends Component<LoadingIndicatorProps> {
  private textElement: HTMLElement | null = null;

  protected render(): HTMLElement {
    const container = createElement('div', {
      class: 'loading-indicator',
    });

    const spinner = createElement('div', {
      class: 'loading-indicator__spinner',
    });

    // Create three dots for animation
    for (let i = 0; i < 3; i++) {
      spinner.appendChild(span({ class: 'loading-indicator__dot' }));
    }

    this.textElement = createElement('div', {
      class: 'loading-indicator__text',
    });
    this.updateMessage();

    container.appendChild(spinner);
    container.appendChild(this.textElement);

    return container;
  }

  /**
   * Update the loading message based on agent type
   * Matches old frontend behavior with agent-specific messages
   */
  private updateMessage(): void {
    if (!this.textElement) return;

    const { message, agentType = 'narrative' } = this.props;

    // If custom message provided, use it
    if (message) {
      this.textElement.textContent = message;
      return;
    }

    // Otherwise, use agent-specific message (matches old frontend)
    let agentMessage = '';
    switch (agentType) {
      case 'combat':
        agentMessage = '⚔️ Combat agent is processing the battle...';
        break;
      case 'summarizer':
        agentMessage = '📝 Summarizer agent is preparing a summary...';
        break;
      case 'narrative':
      default:
        agentMessage = '📖 The Dungeon Master is crafting your adventure...';
        break;
    }

    this.textElement.textContent = agentMessage;
  }

  /**
   * Update the loading indicator with new props
   * Allows updating message dynamically without re-mounting
   */
  public updateProps(props: Partial<LoadingIndicatorProps>): void {
    this.props = { ...this.props, ...props };
    this.updateMessage();
  }
}
