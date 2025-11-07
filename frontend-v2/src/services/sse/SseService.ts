/**
 * Server-Sent Events (SSE) service
 *
 * Manages SSE connections for real-time updates from the backend.
 * Automatically reconnects on connection loss and handles event routing.
 */

import { SseError } from '../../types/errors.js';
import type {
  SSEEventType as BackendSSEEventType,
  ConnectedData,
  HeartbeatData,
  NarrativeData,
  InitialNarrativeData,
  ToolCallData,
  ToolResultData,
  NPCDialogueData,
  PolicyWarningData,
  CombatSuggestionData,
  ScenarioInfoData,
  GameUpdateData,
  CombatUpdateData,
  ErrorData,
  CompleteData,
  SystemMessageData,
} from '../../types/generated/SSEEvent.js';

// Extend backend SSE events with client-only events used by the UI
export type ClientOnlyEventType = 'narrative_chunk' | 'thinking';
export type SseEventType = BackendSSEEventType | ClientOnlyEventType;

// Map backend event type to its payload type
type BackendEventPayload<E extends BackendSSEEventType> =
  E extends 'connected' ? ConnectedData :
  E extends 'heartbeat' ? HeartbeatData :
  E extends 'narrative' ? NarrativeData :
  E extends 'initial_narrative' ? InitialNarrativeData :
  E extends 'tool_call' ? ToolCallData :
  E extends 'tool_result' ? ToolResultData :
  E extends 'npc_dialogue' ? NPCDialogueData :
  E extends 'policy_warning' ? PolicyWarningData :
  E extends 'combat_suggestion' ? CombatSuggestionData :
  E extends 'scenario_info' ? ScenarioInfoData :
  E extends 'game_update' ? GameUpdateData :
  E extends 'combat_update' ? CombatUpdateData :
  E extends 'error' ? ErrorData :
  E extends 'complete' ? CompleteData :
  E extends 'system' ? SystemMessageData :
  E extends 'dice_roll' ? unknown :
  never;

export type TypedSseEvent<E extends SseEventType = SseEventType> =
  E extends BackendSSEEventType
    ? { type: E; data: BackendEventPayload<E> }
    : E extends 'narrative_chunk'
      ? { type: 'narrative_chunk'; data: { content: string; delta: string } }
      : E extends 'thinking'
        ? { type: 'thinking'; data: { content: string } }
        : never;

export type SseEventHandler = (event: TypedSseEvent) => void;
export type SseErrorHandler = (error: Error) => void;

export interface SseServiceConfig {
  baseUrl: string;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

export class SseService {
  private eventSource: EventSource | null = null;
  private readonly baseUrl: string;
  private readonly reconnectDelay: number;
  private readonly maxReconnectAttempts: number;
  private reconnectAttempts: number = 0;
  private reconnectTimeoutId: number | null = null;
  private handlers: Map<SseEventType, Set<SseEventHandler>> = new Map();
  private errorHandlers: Set<SseErrorHandler> = new Set();
  private gameId: string | null = null;
  private isConnecting: boolean = false;

  constructor(config: SseServiceConfig) {
    this.baseUrl = config.baseUrl;
    this.reconnectDelay = config.reconnectDelay ?? 3000;
    this.maxReconnectAttempts = config.maxReconnectAttempts ?? 5;
  }

  /**
   * Connect to SSE stream for a specific game
   */
  connect(gameId: string): void {
    if (this.isConnecting) {
      console.warn('SSE connection already in progress');
      return;
    }

    if (this.eventSource && this.gameId === gameId) {
      console.warn('Already connected to this game');
      return;
    }

    // Close existing connection if any
    this.disconnect();

    this.gameId = gameId;
    this.isConnecting = true;
    this.reconnectAttempts = 0;

    this.createConnection(gameId);
  }

  /**
   * Disconnect from SSE stream
   */
  disconnect(): void {
    if (this.reconnectTimeoutId !== null) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.gameId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  /**
   * Register event handler for specific event type
   */
  on<E extends SseEventType>(eventType: E, handler: (event: TypedSseEvent<E>) => void): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }

    this.handlers.get(eventType)!.add(handler as unknown as SseEventHandler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(eventType);
      if (handlers) {
        handlers.delete(handler as unknown as SseEventHandler);
      }
    };
  }

  /**
   * Register error handler
   */
  onError(handler: SseErrorHandler): () => void {
    this.errorHandlers.add(handler);

    return () => {
      this.errorHandlers.delete(handler);
    };
  }

  /**
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }

  /**
   * Create EventSource connection
   */
  private createConnection(gameId: string): void {
    const url = `${this.baseUrl}/api/game/${gameId}/sse`;

    try {
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('SSE connection opened');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
      };

      this.eventSource.onmessage = (event: MessageEvent) => {
        this.handleMessage(event);
      };

      this.eventSource.onerror = (event: Event) => {
        this.handleError(event);
      };

      // Register handlers for specific event types
      const eventTypes: BackendSSEEventType[] = [
        'connected',
        'narrative',
        'initial_narrative',
        'tool_call',
        'tool_result',
        'npc_dialogue',
        'policy_warning',
        'combat_suggestion',
        'scenario_info',
        'game_update',
        'combat_update',
        'error',
        'complete',
      ];

      eventTypes.forEach(type => {
        this.eventSource!.addEventListener(type, (event: Event) => {
          this.handleTypedEvent(type, event as MessageEvent);
        });
      });

    } catch (error) {
      this.isConnecting = false;
      const sseError = new SseError('Failed to create SSE connection', error);
      this.notifyErrorHandlers(sseError);
    }
  }

  /**
   * Handle incoming SSE message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      console.log('SSE message received:', data);
    } catch (error) {
      console.error('Failed to parse SSE message:', error);
    }
  }

  /**
   * Handle typed SSE event
   */
  private handleTypedEvent(type: SseEventType, event: MessageEvent): void {
    try {
      const parsed = JSON.parse(event.data);
      const typedEvent = { type, data: parsed } as TypedSseEvent;

      // Notify handlers for this event type
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            (handler as unknown as (e: TypedSseEvent) => void)(typedEvent);
          } catch (error) {
            console.error(`Error in SSE handler for ${type}:`, error);
          }
        });
      }
    } catch (error) {
      console.error(`Failed to handle ${type} event:`, error);
    }
  }

  /**
   * Handle connection error
   */
  private handleError(event: Event): void {
    console.error('SSE connection error:', event);

    const error = new SseError('SSE connection error');
    this.notifyErrorHandlers(error);

    // Attempt to reconnect
    if (this.eventSource && this.eventSource.readyState === EventSource.CLOSED) {
      this.attemptReconnect();
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      const error = new SseError('Max reconnection attempts reached');
      this.notifyErrorHandlers(error);
      this.disconnect();
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

    this.reconnectTimeoutId = window.setTimeout(() => {
      if (this.gameId) {
        this.reconnectAttempts++;
        this.createConnection(this.gameId);
      }
    }, delay);
  }

  /**
   * Notify all error handlers
   */
  private notifyErrorHandlers(error: Error): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (err) {
        console.error('Error in SSE error handler:', err);
      }
    });
  }
}
