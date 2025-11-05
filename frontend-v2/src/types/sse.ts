/**
 * SSE event type definitions
 */

export type SseEventType =
  | 'narrative_chunk'
  | 'tool_call'
  | 'game_update'
  | 'combat_update'
  | 'error'
  | 'complete'
  | 'thinking';

export interface SseEvent {
  type: SseEventType;
  data: unknown;
}

export interface NarrativeChunkEvent {
  type: 'narrative_chunk';
  data: {
    content: string;
    delta: string;
  };
}

export interface ToolCallEvent {
  type: 'tool_call';
  data: {
    tool_name: string;
    arguments: Record<string, unknown>;
    result?: unknown;
  };
}

export interface GameUpdateEvent {
  type: 'game_update';
  data: {
    game_state: unknown; // Will be properly typed when we have full game state types
  };
}

export interface CombatUpdateEvent {
  type: 'combat_update';
  data: {
    round: number;
    turn_index: number;
    current_entity: string;
  };
}

export interface ErrorEvent {
  type: 'error';
  data: {
    message: string;
    code?: string;
  };
}

export interface CompleteEvent {
  type: 'complete';
  data: {
    success: boolean;
  };
}

export interface ThinkingEvent {
  type: 'thinking';
  data: {
    content: string;
  };
}

export type TypedSseEvent =
  | NarrativeChunkEvent
  | ToolCallEvent
  | GameUpdateEvent
  | CombatUpdateEvent
  | ErrorEvent
  | CompleteEvent
  | ThinkingEvent;
