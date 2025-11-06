/**
 * SSE event type definitions
 */

export type SseEventType =
  | 'connected'
  | 'narrative'
  | 'narrative_chunk'
  | 'initial_narrative'
  | 'tool_call'
  | 'tool_result'
  | 'npc_dialogue'
  | 'policy_warning'
  | 'combat_suggestion'
  | 'scenario_info'
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

export interface ConnectedEvent {
  type: 'connected';
  data: {
    game_id: string;
    status: 'connected';
    timestamp: string;
  };
}

export interface NarrativeEvent {
  type: 'narrative';
  data: {
    content: string;
    timestamp: string;
  };
}

export interface InitialNarrativeEvent {
  type: 'initial_narrative';
  data: {
    scenario_title: string;
    narrative: string;
    timestamp: string;
  };
}

export interface ToolResultEvent {
  type: 'tool_result';
  data: {
    tool_name: string;
    result: unknown; // ToolResult - will be properly typed when backend types are updated
    timestamp: string;
  };
}

export interface NpcDialogueEvent {
  type: 'npc_dialogue';
  data: {
    npc_id: string;
    npc_name: string;
    content: string;
    complete: boolean;
    timestamp: string;
  };
}

export interface PolicyWarningEvent {
  type: 'policy_warning';
  data: {
    message: string;
    tool_name?: string;
    agent_type?: string;
    timestamp: string;
  };
}

export interface CombatSuggestionEvent {
  type: 'combat_suggestion';
  data: {
    suggestion: import('./generated/CombatSuggestion.js').CombatSuggestion;
    timestamp: string;
  };
}

export interface ScenarioInfoEvent {
  type: 'scenario_info';
  data: {
    current_scenario: unknown; // ScenarioSheet
    available_scenarios: unknown[]; // ScenarioSheet[]
    timestamp: string;
  };
}

export type TypedSseEvent =
  | ConnectedEvent
  | NarrativeEvent
  | NarrativeChunkEvent
  | InitialNarrativeEvent
  | ToolCallEvent
  | ToolResultEvent
  | NpcDialogueEvent
  | PolicyWarningEvent
  | CombatSuggestionEvent
  | ScenarioInfoEvent
  | GameUpdateEvent
  | CombatUpdateEvent
  | ErrorEvent
  | CompleteEvent
  | ThinkingEvent;
