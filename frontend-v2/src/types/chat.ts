/**
 * Chat display message types
 *
 * Extends beyond conversation history messages to include
 * display-only messages from SSE events (tool calls, NPC dialogue, etc.)
 */

import type { Message } from './generated/GameState.js';

/**
 * Message type for display purposes in chat
 */
export type ChatMessageType =
  | 'user'
  | 'assistant'
  | 'system'
  | 'tool'
  | 'tool-result'
  | 'npc'
  | 'policy-warning'
  | 'loading'
  | 'error'
  | 'success';

/**
 * Display message in chat
 * Can be either a conversation history message or a display-only message
 */
export interface ChatDisplayMessage {
  type: ChatMessageType;
  content: string;
  timestamp?: string;

  // Additional metadata for specific message types
  metadata?: {
    // For tool messages
    toolName?: string;
    parameters?: Record<string, unknown>;

    // For tool result messages
    result?: unknown;

    // For NPC dialogue
    npcId?: string;
    npcName?: string;

    // For policy warnings
    agentType?: string;
  };
}

/**
 * Convert a conversation Message to a ChatDisplayMessage
 * Preserves NPC metadata from conversation history
 */
export function messageToDisplayMessage(message: Message): ChatDisplayMessage {
  const displayMessage: ChatDisplayMessage = {
    type: message.role as ChatMessageType,
    content: message.content,
    timestamp: message.timestamp ?? undefined,
  };

  // Preserve NPC speaker metadata for NPC messages
  if (message.role === 'npc' && (message.speaker_npc_id || message.speaker_npc_name)) {
    displayMessage.metadata = {
      npcId: message.speaker_npc_id ?? undefined,
      npcName: message.speaker_npc_name ?? undefined,
    };
  }

  return displayMessage;
}
