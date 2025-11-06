/**
 * ChatMessage component
 *
 * Renders an individual chat message with role-based styling.
 * Supports user messages, assistant messages, and system messages.
 * Renders markdown formatting in message content.
 */

import { Component } from '../base/Component.js';
import { createElement } from '../../utils/dom.js';
import { setMarkdownContent } from '../../utils/markdown.js';
import type { Message } from '../../types/generated/GameState.js';

export interface ChatMessageProps {
  message: Message;
}

export class ChatMessage extends Component<ChatMessageProps> {
  protected render(): HTMLElement {
    const { message } = this.props;

    const messageDiv = createElement('div', {
      class: `chat-message chat-message--${message.role}`,
      'data-role': message.role,
      'data-timestamp': message.timestamp ?? '',
    });

    // Role label
    const roleLabel = createElement('div', {
      class: 'chat-message__role',
    });
    roleLabel.textContent = this.getRoleLabel(message.role);

    // Message content (with markdown rendering)
    const content = createElement('div', {
      class: 'chat-message__content',
    });
    setMarkdownContent(content, message.content);

    // Timestamp
    const timestamp = createElement('div', {
      class: 'chat-message__timestamp',
    });
    timestamp.textContent = this.formatTimestamp(message.timestamp ?? '');

    messageDiv.appendChild(roleLabel);
    messageDiv.appendChild(content);
    messageDiv.appendChild(timestamp);

    return messageDiv;
  }

  private getRoleLabel(role: string): string {
    switch (role) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'DM';
      case 'system':
        return 'System';
      default:
        return role;
    }
  }

  private formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  }
}
