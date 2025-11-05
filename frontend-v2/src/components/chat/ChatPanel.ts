/**
 * ChatPanel component
 *
 * Main chat interface containing message history, loading indicator, and input.
 * Automatically scrolls to bottom on new messages.
 */

import { Component } from '../base/Component.js';
import { createElement, clearElement } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { ChatMessage } from './ChatMessage.js';
import { ChatInput } from './ChatInput.js';
import { LoadingIndicator } from './LoadingIndicator.js';
import { ConversationEntry } from '../../types/generated/GameState.js';

export interface ChatPanelProps {
  stateStore: StateStore;
  onSendMessage: (message: string) => void;
}

export class ChatPanel extends Component<ChatPanelProps> {
  private messagesContainer: HTMLElement | null = null;
  private chatInput: ChatInput | null = null;
  private loadingIndicator: LoadingIndicator | null = null;
  private messageComponents: Map<string, ChatMessage> = new Map();

  protected render(): HTMLElement {
    const container = createElement('div', {
      class: 'chat-panel',
    });

    // Header
    const header = createElement('div', {
      class: 'chat-panel__header',
    });
    const title = createElement('h2', {
      class: 'chat-panel__title',
    });
    title.textContent = 'Chat';
    header.appendChild(title);

    // Messages container (scrollable)
    this.messagesContainer = createElement('div', {
      class: 'chat-panel__messages',
    });

    // Input container
    const inputContainer = createElement('div', {
      class: 'chat-panel__input',
    });

    container.appendChild(header);
    container.appendChild(this.messagesContainer);
    container.appendChild(inputContainer);

    // Create chat input
    this.chatInput = new ChatInput({
      onSubmit: (message) => this.handleSendMessage(message),
      placeholder: 'Type your action... (Enter to send, Shift+Enter for new line)',
    });

    // Create loading indicator (initially not mounted)
    this.loadingIndicator = new LoadingIndicator({
      message: 'AI is thinking...',
    });

    // Mount chat input
    this.chatInput.mount(inputContainer);

    return container;
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribeImmediate(
      this.props.stateStore['gameState'],
      (gameState) => {
        if (gameState) {
          this.renderMessages(gameState.conversation_history);
        } else {
          this.clearMessages();
        }
      }
    );

    // Subscribe to processing state
    this.subscribe(
      this.props.stateStore['isProcessing'],
      (isProcessing) => {
        this.updateProcessingState(isProcessing);
      }
    );
  }

  override onUnmount(): void {
    // Clean up message components
    this.messageComponents.forEach(comp => comp.unmount());
    this.messageComponents.clear();

    // Clean up input
    if (this.chatInput) {
      this.chatInput.unmount();
      this.chatInput = null;
    }

    // Clean up loading indicator
    if (this.loadingIndicator) {
      this.loadingIndicator.unmount();
      this.loadingIndicator = null;
    }
  }

  private renderMessages(messages: ConversationEntry[]): void {
    if (!this.messagesContainer) return;

    // Clear existing messages
    clearElement(this.messagesContainer);
    this.messageComponents.forEach(comp => comp.unmount());
    this.messageComponents.clear();

    // Render each message
    messages.forEach((message, index) => {
      const messageComp = new ChatMessage({ message });
      messageComp.mount(this.messagesContainer!);
      this.messageComponents.set(`${index}-${message.timestamp}`, messageComp);
    });

    // Scroll to bottom
    this.scrollToBottom();
  }

  private clearMessages(): void {
    if (!this.messagesContainer) return;

    clearElement(this.messagesContainer);
    this.messageComponents.forEach(comp => comp.unmount());
    this.messageComponents.clear();
  }

  private updateProcessingState(isProcessing: boolean): void {
    if (!this.messagesContainer || !this.loadingIndicator) return;

    if (isProcessing) {
      // Show loading indicator
      this.loadingIndicator.mount(this.messagesContainer);
      this.scrollToBottom();

      // Disable input
      this.chatInput?.setDisabled(true);
    } else {
      // Hide loading indicator
      if (this.loadingIndicator.isMountedToDOM()) {
        this.loadingIndicator.unmount();
      }

      // Enable input
      this.chatInput?.setDisabled(false);
      this.chatInput?.focus();
    }
  }

  private handleSendMessage(message: string): void {
    this.props.onSendMessage(message);
  }

  private scrollToBottom(): void {
    if (!this.messagesContainer) return;

    // Scroll to bottom with smooth behavior
    setTimeout(() => {
      this.messagesContainer!.scrollTop = this.messagesContainer!.scrollHeight;
    }, 0);
  }
}
