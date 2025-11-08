/**
 * Service responsible for formatting tool execution results into human-readable messages.
 * Extracted from GameInterfaceScreen to follow Single Responsibility Principle.
 *
 * Uses auto-generated types from backend for type safety.
 */

import { LevelUpResult } from '../../types/generated/LevelUpResult.js';
import { RollDiceResult } from '../../types/generated/RollDiceResult.js';

/**
 * Service for formatting tool execution results into display-friendly messages
 */
export class ToolResultFormatterService {
  /**
   * Formats a tool execution result based on its type
   * @param toolName - Name of the tool that was executed
   * @param result - The result returned by the tool (from backend)
   * @returns A formatted string suitable for display in chat
   */
  formatResult(toolName: string, result: unknown): string {
    if (typeof result === 'object' && result !== null) {
      if (this.isLevelUpResult(result)) {
        return this.formatLevelUp(result);
      }
      if (this.isRollDiceResult(result)) {
        return this.formatDiceRoll(result);
      }
      return this.formatGeneric(toolName, result);
    }

    // Primitive result (shouldn't happen with current backend typing)
    return `✓ ${toolName} completed: ${String(result)}`;
  }

  /**
   * Type guard: checks if result is a LevelUpResult
   */
  private isLevelUpResult(result: unknown): result is LevelUpResult {
    return (
      typeof result === 'object' &&
      result !== null &&
      'type' in result &&
      (result as { type: unknown }).type === 'level_up'
    );
  }

  /**
   * Type guard: checks if result is a RollDiceResult
   */
  private isRollDiceResult(result: unknown): result is RollDiceResult {
    return (
      typeof result === 'object' &&
      result !== null &&
      'roll_type' in result &&
      'dice' in result &&
      'total' in result
    );
  }

  /**
   * Formats a level-up result
   * @example "⬆️ Level Up: 3 → 4 (HP +8)"
   */
  private formatLevelUp(result: LevelUpResult): string {
    return `⬆️ Level Up: ${result.old_level} → ${result.new_level} (HP +${result.hp_increase})`;
  }

  /**
   * Formats a dice roll result with modifiers, rolls, and critical indicators
   * @example "📊 Attack Roll: 1d20+5 = 23 [18] (Dexterity - Acrobatics) - 🎯 CRITICAL!"
   */
  private formatDiceRoll(result: RollDiceResult): string {
    const parts: string[] = [];

    // Roll type and base notation
    const rollType = result.roll_type.charAt(0).toUpperCase() + result.roll_type.slice(1);
    const modifier = result.modifier ?? 0;
    const modStr = modifier !== 0 ? (modifier > 0 ? `+${modifier}` : `${modifier}`) : '';

    parts.push(`📊 ${rollType} Roll: ${result.dice}${modStr} = ${result.total}`);

    // Individual roll values
    const rolls = result.rolls ?? [];
    if (rolls.length > 0) {
      parts.push(` [${rolls.join(', ')}]`);
    }

    // Ability and skill context
    if (result.ability) {
      const skillSuffix = result.skill ? ` - ${result.skill}` : '';
      parts.push(` (${result.ability}${skillSuffix})`);
    }

    // Critical success/failure
    if (result.critical === true) {
      parts.push(' - 🎯 CRITICAL!');
    } else if (result.critical === false && rolls.includes(1)) {
      parts.push(' - 💀 CRITICAL FAIL!');
    }

    return parts.join('');
  }

  /**
   * Formats a generic tool result (fallback for unknown result types)
   * @example "✓ add_item completed: {"item_id":"sword-001","quantity":1}"
   */
  private formatGeneric(toolName: string, result: unknown): string {
    return `✓ ${toolName} completed: ${JSON.stringify(result)}`;
  }
}
