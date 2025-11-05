/**
 * Server-Sent Events (SSE) service
 *
 * Manages SSE connections for real-time updates from the backend.
 * Automatically reconnects on connection loss and handles event routing.
 */

import { SseError } from '../../types/errors.js';
import { TypedSseEvent, SseEventType } from '../../types/sse.js';

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
  on(eventType: SseEventType, handler: SseEventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }

    this.handlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
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
      const eventTypes: SseEventType[] = [
        'narrative_chunk',
        'tool_call',
        'game_update',
        'combat_update',
        'error',
        'complete',
        'thinking',
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
      const data = JSON.parse(event.data);
      const typedEvent: TypedSseEvent = { type, data } as TypedSseEvent;

      // Notify handlers for this event type
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(typedEvent);
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
