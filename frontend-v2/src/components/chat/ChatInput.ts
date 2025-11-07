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
  private submitBtn: HTMLButtonElement | null = null;
  private originalPlaceholder: string = '';
  private originalButtonText: string = 'Send';

  protected render(): HTMLElement {
    const { placeholder = 'Type your action...', disabled = false } = this.props;

    // Store original values for restoration
    this.originalPlaceholder = placeholder;
    this.originalButtonText = 'Send';

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
    const submitBtnElement = button(this.originalButtonText, {
      class: 'chat-input__submit',
      disabled: disabled,
      onClick: () => this.handleSubmit(),
    });
    this.submitBtn = submitBtnElement as HTMLButtonElement;

    container.appendChild(this.textarea);
    container.appendChild(submitBtnElement);

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
    if (this.submitBtn) {
      this.submitBtn.disabled = disabled;
    }
  }

  /**
   * Update placeholder text
   * Used to show "Waiting for agent response..." during processing
   */
  setPlaceholder(placeholder: string): void {
    if (this.textarea) {
      this.textarea.placeholder = placeholder;
    }
  }

  /**
   * Restore original placeholder
   */
  restorePlaceholder(): void {
    this.setPlaceholder(this.originalPlaceholder);
  }

  /**
   * Update button text
   * Used to show "Agent is thinking..." during processing
   */
  setButtonText(text: string): void {
    if (this.submitBtn) {
      this.submitBtn.textContent = text;
    }
  }

  /**
   * Restore original button text
   */
  restoreButtonText(): void {
    this.setButtonText(this.originalButtonText);
  }
}
