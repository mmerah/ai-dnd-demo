/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type ToolName = string;

/**
 * Data for tool call events.
 */
export interface ToolCallData {
  timestamp?: Timestamp;
  tool_name: ToolName;
  parameters: Parameters;
}
export interface Parameters {
  [k: string]:
    | string
    | number
    | boolean
    | {
        [k: string]: any;
      }
    | any[]
    | null;
}
