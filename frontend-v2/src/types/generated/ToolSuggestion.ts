/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Name of the suggested tool
 */
export type ToolName = string;
/**
 * Explanation for why this tool should be used
 */
export type Reason = string;
/**
 * Confidence level in this suggestion (0.0-1.0)
 */
export type Confidence = number;
/**
 * Optional suggested arguments for the tool
 */
export type Arguments = {
  [k: string]: any;
} | null;

/**
 * A suggestion to use a specific tool with reasoning and confidence.
 */
export interface ToolSuggestion {
  tool_name: ToolName;
  reason: Reason;
  confidence: Confidence;
  arguments?: Arguments;
}
