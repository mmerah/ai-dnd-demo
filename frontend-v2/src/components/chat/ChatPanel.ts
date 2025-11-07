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
import type { Message } from '../../types/generated/GameState.js';
import { messageToDisplayMessage, type ChatDisplayMessage } from '../../types/chat.js';

export interface ChatPanelProps {
  stateStore: StateStore;
  onSendMessage: (message: string) => void;
}

export class ChatPanel extends Component<ChatPanelProps> {
  private messagesContainer: HTMLElement | null = null;
  private chatInput: ChatInput | null = null;
  private loadingIndicator: LoadingIndicator | null = null;
  private suggestionContainer: HTMLElement | null = null;
  private messageComponents: Map<string, ChatMessage> = new Map();
  private realtimeMessageCounter: number = 0;
  private hasLoadedInitialMessages: boolean = false;

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

    // Suggestion container (sits above the input at the bottom)
    this.suggestionContainer = createElement('div', {
      class: 'chat-panel__suggestion',
    });

    // Input container
    const inputContainer = createElement('div', {
      class: 'chat-panel__input',
    });

    container.appendChild(header);
    container.appendChild(this.messagesContainer);
    container.appendChild(this.suggestionContainer);
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
    // IMPORTANT: Only load conversation_history on initial mount
    // After that, rely on SSE events to add new messages in real-time
    this.subscribeImmediate(
      this.props.stateStore.gameState$,
      (gameState) => {
        if (gameState) {
          // Only render messages from conversation_history if we haven't loaded initial messages yet
          // This prevents wiping out real-time SSE messages when game state updates
          if (!this.hasLoadedInitialMessages) {
            this.renderMessages(gameState.conversation_history ?? []);
            this.hasLoadedInitialMessages = true;
          }
        } else {
          // Game state cleared (e.g., exiting game) - reset everything
          this.clearMessages();
          this.hasLoadedInitialMessages = false;
        }
      }
    );

    // Subscribe to processing state
    this.subscribe(
      this.props.stateStore.isProcessing$,
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

    // Clean up suggestion container
    if (this.suggestionContainer) {
      this.suggestionContainer.innerHTML = '';
      this.suggestionContainer = null;
    }
  }

  private renderMessages(messages: Message[]): void {
    if (!this.messagesContainer) return;

    // Clear existing messages
    clearElement(this.messagesContainer);
    this.messageComponents.forEach(comp => comp.unmount());
    this.messageComponents.clear();

    // Render each message
    messages.forEach((message, index) => {
      const displayMessage = messageToDisplayMessage(message);
      const messageComp = new ChatMessage({ message: displayMessage });
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
      // Update loading indicator with current agent type
      const gameState = this.props.stateStore.getGameState();
      const agentType = gameState?.active_agent || 'narrative';
      this.loadingIndicator.updateProps({ agentType });

      // Show loading indicator
      this.loadingIndicator.mount(this.messagesContainer);
      this.scrollToBottom();

      // Disable input and update UI to show processing state
      this.chatInput?.setDisabled(true);
      this.chatInput?.setPlaceholder('Waiting for agent response...');
      this.chatInput?.setButtonText('Agent is thinking...');
    } else {
      // Hide loading indicator
      if (this.loadingIndicator.isMountedToDOM()) {
        this.loadingIndicator.unmount();
      }

      // Enable input and restore original UI
      this.chatInput?.setDisabled(false);
      this.chatInput?.restorePlaceholder();
      this.chatInput?.restoreButtonText();
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

  /**
   * Add a real-time message to chat (from SSE events)
   * These messages are ephemeral and won't be in conversation_history until the next state reload
   * Returns the message key for later updates
   */
  public addRealtimeMessage(message: ChatDisplayMessage): string {
    if (!this.messagesContainer) {
      console.warn('Cannot add realtime message: messages container not mounted');
      return '';
    }

    // Create unique key for this realtime message
    const key = `realtime-${this.realtimeMessageCounter++}-${Date.now()}`;

    // Create and mount the message component
    const messageComp = new ChatMessage({ message });
    messageComp.mount(this.messagesContainer);
    this.messageComponents.set(key, messageComp);

    // Scroll to show the new message
    this.scrollToBottom();

    return key;
  }

  /**
   * Update an existing message's content (for streaming)
   * Used for accumulating narrative chunks
   */
  public updateMessage(messageKey: string, newContent: string): void {
    const messageComp = this.messageComponents.get(messageKey);
    if (!messageComp) {
      console.warn(`[ChatPanel] Cannot update message: key "${messageKey}" not found`);
      return;
    }

    messageComp.updateContent(newContent);
    this.scrollToBottom();
  }

  /**
   * Focus the chat input (for external control)
   */
  public focusInput(): void {
    this.chatInput?.focus();
  }

  /**
   * Mount a suggestion component just above the input area
   */
  public mountSuggestionCard(card: Component<any>): void {
    if (!this.suggestionContainer) {
      console.warn('[ChatPanel] Suggestion container not available');
      return;
    }
    card.mount(this.suggestionContainer);
  }
}
