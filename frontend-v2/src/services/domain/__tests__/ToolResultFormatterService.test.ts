import { describe, it, expect } from 'vitest';
import { ToolResultFormatterService } from '../ToolResultFormatterService';

describe('ToolResultFormatterService', () => {
  const service = new ToolResultFormatterService();

  describe('formatResult', () => {
    describe('LevelUpResult formatting', () => {
      it('should format level up result with emoji and HP increase', () => {
        const result = {
          type: 'level_up',
          target: 'player-1',
          old_level: 3,
          new_level: 4,
          old_max_hp: 24,
          new_max_hp: 32,
          hp_increase: 8,
          message: 'Level up!',
        };

        const formatted = service.formatResult('level_up', result);

        expect(formatted).toBe('⬆️ Level Up: 3 → 4 (HP +8)');
      });

      it('should handle level 1 to level 2', () => {
        const result = {
          type: 'level_up',
          target: 'player-1',
          old_level: 1,
          new_level: 2,
          old_max_hp: 10,
          new_max_hp: 16,
          hp_increase: 6,
          message: 'Level up!',
        };

        const formatted = service.formatResult('level_up', result);

        expect(formatted).toBe('⬆️ Level Up: 1 → 2 (HP +6)');
      });

      it('should handle higher levels (e.g., 19 to 20)', () => {
        const result = {
          type: 'level_up',
          target: 'player-1',
          old_level: 19,
          new_level: 20,
          old_max_hp: 142,
          new_max_hp: 150,
          hp_increase: 8,
          message: 'Level up!',
        };

        const formatted = service.formatResult('level_up', result);

        expect(formatted).toBe('⬆️ Level Up: 19 → 20 (HP +8)');
      });
    });

    describe('RollDiceResult formatting', () => {
      it('should format basic roll without modifier', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'attack',
          dice: '1d20',
          modifier: 0,
          rolls: [15],
          total: 15,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Attack Roll: 1d20 = 15 [15]');
      });

      it('should format roll with positive modifier', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'attack',
          dice: '1d20',
          modifier: 5,
          rolls: [18],
          total: 23,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Attack Roll: 1d20+5 = 23 [18]');
      });

      it('should format roll with negative modifier', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'saving throw',
          dice: '1d20',
          modifier: -2,
          rolls: [12],
          total: 10,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Saving throw Roll: 1d20-2 = 10 [12]');
      });

      it('should format roll with ability', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'ability check',
          dice: '1d20',
          modifier: 3,
          rolls: [14],
          total: 17,
          ability: 'Dexterity',
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Ability check Roll: 1d20+3 = 17 [14] (Dexterity)');
      });

      it('should format roll with ability and skill', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'skill check',
          dice: '1d20',
          modifier: 5,
          rolls: [18],
          total: 23,
          ability: 'Dexterity',
          skill: 'Acrobatics',
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe(
          '📊 Skill check Roll: 1d20+5 = 23 [18] (Dexterity - Acrobatics)'
        );
      });

      it('should format critical success', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'attack',
          dice: '1d20',
          modifier: 5,
          rolls: [20],
          total: 25,
          critical: true,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Attack Roll: 1d20+5 = 25 [20] - 🎯 CRITICAL!');
      });

      it('should format critical failure (nat 1)', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'attack',
          dice: '1d20',
          modifier: 5,
          rolls: [1],
          total: 6,
          critical: false,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Attack Roll: 1d20+5 = 6 [1] - 💀 CRITICAL FAIL!');
      });

      it('should format damage roll (multiple dice)', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'damage',
          dice: '2d6',
          modifier: 3,
          rolls: [4, 5],
          total: 12,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Damage Roll: 2d6+3 = 12 [4, 5]');
      });

      it('should handle empty rolls array', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'check',
          dice: '1d20',
          modifier: 2,
          rolls: [],
          total: 10,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Check Roll: 1d20+2 = 10');
      });

      it('should capitalize roll type', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'initiative',
          dice: '1d20',
          modifier: 2,
          rolls: [15],
          total: 17,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Initiative Roll: 1d20+2 = 17 [15]');
      });
    });

    describe('Generic result formatting', () => {
      it('should format unknown object result as JSON', () => {
        const result = {
          item_id: 'sword-001',
          quantity: 1,
        };

        const formatted = service.formatResult('add_item', result);

        expect(formatted).toBe(
          '✓ add_item completed: {"item_id":"sword-001","quantity":1}'
        );
      });

      it('should handle complex nested objects', () => {
        const result = {
          type: 'custom',
          data: {
            nested: {
              value: 42,
            },
          },
        };

        const formatted = service.formatResult('custom_tool', result);

        expect(formatted).toBe(
          '✓ custom_tool completed: {"type":"custom","data":{"nested":{"value":42}}}'
        );
      });

      it('should handle arrays in result', () => {
        const result = {
          items: ['item-1', 'item-2', 'item-3'],
        };

        const formatted = service.formatResult('get_items', result);

        expect(formatted).toBe(
          '✓ get_items completed: {"items":["item-1","item-2","item-3"]}'
        );
      });
    });

    describe('Primitive result handling', () => {
      it('should handle string result', () => {
        const formatted = service.formatResult('test_tool', 'success');

        expect(formatted).toBe('✓ test_tool completed: success');
      });

      it('should handle number result', () => {
        const formatted = service.formatResult('calculate', 42);

        expect(formatted).toBe('✓ calculate completed: 42');
      });

      it('should handle boolean result', () => {
        const formatted = service.formatResult('check_condition', true);

        expect(formatted).toBe('✓ check_condition completed: true');
      });

      it('should handle null result', () => {
        const formatted = service.formatResult('nullable_tool', null);

        expect(formatted).toBe('✓ nullable_tool completed: null');
      });

      it('should handle undefined result', () => {
        const formatted = service.formatResult('undefined_tool', undefined);

        expect(formatted).toBe('✓ undefined_tool completed: undefined');
      });
    });

    describe('Edge cases', () => {
      it('should handle result with null ability', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'check',
          dice: '1d20',
          modifier: 0,
          rolls: [10],
          total: 10,
          ability: null,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Check Roll: 1d20 = 10 [10]');
      });

      it('should handle result with null skill', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'check',
          dice: '1d20',
          modifier: 0,
          rolls: [10],
          total: 10,
          ability: 'Strength',
          skill: null,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Check Roll: 1d20 = 10 [10] (Strength)');
      });

      it('should handle result with null critical', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'check',
          dice: '1d20',
          modifier: 0,
          rolls: [10],
          total: 10,
          critical: null,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Check Roll: 1d20 = 10 [10]');
      });

      it('should not show critical fail for non-1 roll when critical is false', () => {
        const result = {
          type: 'dice_roll',
          roll_type: 'attack',
          dice: '1d20',
          modifier: 5,
          rolls: [10],
          total: 15,
          critical: false,
        };

        const formatted = service.formatResult('roll_dice', result);

        expect(formatted).toBe('📊 Attack Roll: 1d20+5 = 15 [10]');
      });

      it('should handle empty object result', () => {
        const formatted = service.formatResult('empty_tool', {});

        expect(formatted).toBe('✓ empty_tool completed: {}');
      });
    });
  });
});
