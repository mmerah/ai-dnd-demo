/**
 * ChatMessage component
 *
 * Renders an individual chat message with type-based styling.
 * Supports multiple message types including conversation messages,
 * tool calls, NPC dialogue, warnings, and system messages.
 */

import { Component } from '../base/Component.js';
import { createElement } from '../../utils/dom.js';
import { setMarkdownContent } from '../../utils/markdown.js';
import type { ChatDisplayMessage } from '../../types/chat.js';

export interface ChatMessageProps {
  message: ChatDisplayMessage;
}

export class ChatMessage extends Component<ChatMessageProps> {
  protected render(): HTMLElement {
    const { message } = this.props;

    const messageDiv = createElement('div', {
      class: `chat-message chat-message--${message.type}`,
      'data-type': message.type,
      'data-timestamp': message.timestamp ?? '',
    });

    // Render based on message type
    switch (message.type) {
      case 'npc':
        this.renderNpcMessage(messageDiv, message);
        break;
      case 'tool':
        this.renderToolMessage(messageDiv, message);
        break;
      case 'tool-result':
        this.renderToolResultMessage(messageDiv, message);
        break;
      case 'policy-warning':
        this.renderPolicyWarningMessage(messageDiv, message);
        break;
      case 'error':
      case 'success':
      case 'loading':
        this.renderStatusMessage(messageDiv, message);
        break;
      default:
        this.renderStandardMessage(messageDiv, message);
        break;
    }

    return messageDiv;
  }

  /**
   * Render NPC dialogue message with speaker name
   */
  private renderNpcMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    const speakerName = message.metadata?.npcName ?? 'NPC';

    const speakerEl = createElement('div', {
      class: 'chat-message__speaker',
    });
    speakerEl.textContent = speakerName;

    const contentEl = createElement('div', {
      class: 'chat-message__content',
    });
    contentEl.textContent = message.content;

    container.appendChild(speakerEl);
    container.appendChild(contentEl);

    if (message.timestamp) {
      container.appendChild(this.createTimestamp(message.timestamp));
    }
  }

  /**
   * Render tool call message with formatted parameters
   */
  private renderToolMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    const toolName = message.metadata?.toolName ?? 'Unknown Tool';
    const parameters = message.metadata?.parameters ?? {};

    const iconEl = createElement('span', {
      class: 'chat-message__icon',
    });
    iconEl.textContent = '🎲';

    const contentEl = createElement('div', {
      class: 'chat-message__content',
    });

    // Format tool name
    let toolText = toolName;

    // Add parameters if present
    if (Object.keys(parameters).length > 0) {
      const paramsText = this.formatToolParameters(toolName, parameters);
      if (paramsText) {
        toolText += ` ${paramsText}`;
      }
    }

    contentEl.textContent = toolText;

    container.appendChild(iconEl);
    container.appendChild(contentEl);

    if (message.timestamp) {
      container.appendChild(this.createTimestamp(message.timestamp));
    }
  }

  /**
   * Format tool parameters for display
   */
  private formatToolParameters(toolName: string, parameters: Record<string, unknown>): string {
    // Special formatting for dice rolls
    if (toolName.includes('roll')) {
      const parts: string[] = [];

      if (parameters['ability']) {
        parts.push(`- ${parameters['ability']}`);
      }
      if (parameters['skill']) {
        parts.push(`(${parameters['skill']})`);
      }
      if (parameters['dc'] !== undefined) {
        parts.push(`DC ${parameters['dc']}`);
      }
      if (parameters['purpose']) {
        parts.push(`for ${parameters['purpose']}`);
      }

      return parts.join(' ');
    }

    // Generic parameter display for other tools
    const filteredParams = Object.entries(parameters)
      .filter(([key]) => key !== 'raw_args')
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');

    return filteredParams ? `(${filteredParams})` : '';
  }

  /**
   * Render tool result message with formatted output
   */
  private renderToolResultMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    const iconEl = createElement('span', {
      class: 'chat-message__icon',
    });
    iconEl.textContent = '📊';

    const contentEl = createElement('div', {
      class: 'chat-message__content',
    });
    contentEl.textContent = message.content;

    container.appendChild(iconEl);
    container.appendChild(contentEl);

    if (message.timestamp) {
      container.appendChild(this.createTimestamp(message.timestamp));
    }
  }

  /**
   * Render policy warning message
   */
  private renderPolicyWarningMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    const iconEl = createElement('span', {
      class: 'chat-message__icon',
    });
    iconEl.textContent = '⚠️';

    const contentEl = createElement('div', {
      class: 'chat-message__content',
    });

    let warningText = message.content;

    // Add tool/agent info if present
    const details: string[] = [];
    if (message.metadata?.toolName) {
      details.push(`tool: ${message.metadata.toolName}`);
    }
    if (message.metadata?.agentType) {
      details.push(`agent: ${message.metadata.agentType}`);
    }

    if (details.length > 0) {
      warningText += ` (${details.join(', ')})`;
    }

    contentEl.textContent = warningText;

    container.appendChild(iconEl);
    container.appendChild(contentEl);

    if (message.timestamp) {
      container.appendChild(this.createTimestamp(message.timestamp));
    }
  }

  /**
   * Render status message (error, success, loading)
   */
  private renderStatusMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    const contentEl = createElement('div', {
      class: 'chat-message__content',
    });
    contentEl.textContent = message.content;

    container.appendChild(contentEl);

    if (message.timestamp) {
      container.appendChild(this.createTimestamp(message.timestamp));
    }
  }

  /**
   * Render standard message (user, assistant, system)
   */
  private renderStandardMessage(container: HTMLElement, message: ChatDisplayMessage): void {
    // Role label
    const roleLabel = createElement('div', {
      class: 'chat-message__role',
    });
    roleLabel.textContent = this.getRoleLabel(message.type);

    // Message content (with markdown rendering for assistant messages)
    const content = createElement('div', {
      class: 'chat-message__content',
    });

    if (message.type === 'assistant') {
      setMarkdownContent(content, message.content);
    } else {
      content.textContent = message.content;
    }

    // Timestamp
    const timestamp = this.createTimestamp(message.timestamp ?? '');

    container.appendChild(roleLabel);
    container.appendChild(content);
    container.appendChild(timestamp);
  }

  /**
   * Create timestamp element
   */
  private createTimestamp(timestamp: string): HTMLElement {
    const timestampEl = createElement('div', {
      class: 'chat-message__timestamp',
    });
    timestampEl.textContent = this.formatTimestamp(timestamp);
    return timestampEl;
  }

  /**
   * Get display label for message role
   */
  private getRoleLabel(type: string): string {
    switch (type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'DM';
      case 'system':
        return 'System';
      default:
        return type;
    }
  }

  /**
   * Format timestamp for display
   */
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
