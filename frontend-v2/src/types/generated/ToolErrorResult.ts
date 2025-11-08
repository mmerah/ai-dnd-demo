/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type Error = string;
export type ToolName = string;
export type Suggestion = string | null;

export interface ToolErrorResult {
  type?: Type;
  error: Error;
  tool_name: ToolName;
  suggestion?: Suggestion;
}
