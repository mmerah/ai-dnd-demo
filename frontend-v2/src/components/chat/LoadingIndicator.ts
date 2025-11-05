/**
 * LoadingIndicator component
 *
 * Displays an animated loading indicator when the AI is thinking.
 */

import { Component } from '../base/Component.js';
import { createElement, span } from '../../utils/dom.js';

export interface LoadingIndicatorProps {
  message?: string;
}

export class LoadingIndicator extends Component<LoadingIndicatorProps> {
  protected render(): HTMLElement {
    const { message = 'AI is thinking...' } = this.props;

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

    const text = createElement('div', {
      class: 'loading-indicator__text',
    });
    text.textContent = message;

    container.appendChild(spinner);
    container.appendChild(text);

    return container;
  }
}
