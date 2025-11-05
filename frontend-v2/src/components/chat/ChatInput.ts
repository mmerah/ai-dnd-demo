/**
 * ChatInput component
 *
 * Text input area for sending messages with submit button.
 * Handles Enter key to submit and Shift+Enter for newlines.
 */

import { Component } from '../base/Component.js';
import { createElement, button } from '../../utils/dom.js';

export interface ChatInputProps {
  onSubmit: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export class ChatInput extends Component<ChatInputProps> {
  private textarea: HTMLTextAreaElement | null = null;

  protected render(): HTMLElement {
    const { placeholder = 'Type your action...', disabled = false } = this.props;

    const container = createElement('div', {
      class: 'chat-input',
    });

    // Textarea
    this.textarea = document.createElement('textarea');
    this.textarea.className = 'chat-input__textarea';
    this.textarea.placeholder = placeholder;
    this.textarea.disabled = disabled;
    this.textarea.rows = 3;

    // Handle Enter key
    this.textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit();
      }
    });

    // Submit button
    const submitBtn = button('Send', {
      class: 'chat-input__submit',
      disabled: disabled,
      onClick: () => this.handleSubmit(),
    });

    container.appendChild(this.textarea);
    container.appendChild(submitBtn);

    return container;
  }

  private handleSubmit(): void {
    if (!this.textarea) return;

    const message = this.textarea.value.trim();
    if (!message) return;

    this.props.onSubmit(message);
    this.textarea.value = '';
    this.textarea.focus();
  }

  /**
   * Focus the input
   */
  focus(): void {
    this.textarea?.focus();
  }

  /**
   * Clear the input
   */
  clear(): void {
    if (this.textarea) {
      this.textarea.value = '';
    }
  }

  /**
   * Set disabled state
   */
  setDisabled(disabled: boolean): void {
    if (this.textarea) {
      this.textarea.disabled = disabled;
    }
    const submitBtn = this.element?.querySelector('.chat-input__submit') as HTMLButtonElement;
    if (submitBtn) {
      submitBtn.disabled = disabled;
    }
  }
}
