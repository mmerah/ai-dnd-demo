/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type Message = string;
export type ToolName = string | null;
export type AgentType = string | null;

/**
 * Data for explicit policy warning events (tool gating, etc.).
 */
export interface PolicyWarningData {
  timestamp?: Timestamp;
  message: Message;
  tool_name?: ToolName;
  agent_type?: AgentType;
}
