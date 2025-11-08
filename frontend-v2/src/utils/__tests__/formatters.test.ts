/**
 * Tests for Formatting Utilities
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  formatTimestamp,
  formatCurrency,
  formatModifier,
  formatDiceNotation,
  formatHitPoints,
  formatAbilityScore,
  formatOrdinal,
  formatNumberAbbreviated,
  formatDistance,
  formatWeight,
  formatDuration,
  formatSpellLevel,
  formatProficiencyBonus,
  pluralize,
  type CurrencyValues,
} from '../formatters.js';

describe('formatTimestamp', () => {
  beforeEach(() => {
    // Mock Date.now() to return a fixed time
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-11-08T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return "just now" for very recent timestamps', () => {
    const timestamp = new Date('2025-11-08T11:59:55Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('just now');
  });

  it('should format seconds ago', () => {
    const timestamp = new Date('2025-11-08T11:59:30Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('30 seconds ago');
  });

  it('should format 1 second ago (singular)', () => {
    const timestamp = new Date('2025-11-08T11:59:50Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('10 seconds ago');
  });

  it('should format minutes ago', () => {
    const timestamp = new Date('2025-11-08T11:57:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('3 minutes ago');
  });

  it('should format 1 minute ago (singular)', () => {
    const timestamp = new Date('2025-11-08T11:59:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('1 minute ago');
  });

  it('should format hours ago', () => {
    const timestamp = new Date('2025-11-08T09:00:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('3 hours ago');
  });

  it('should format 1 hour ago (singular)', () => {
    const timestamp = new Date('2025-11-08T11:00:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('1 hour ago');
  });

  it('should format days ago', () => {
    const timestamp = new Date('2025-11-06T12:00:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('2 days ago');
  });

  it('should format 1 day ago (singular)', () => {
    const timestamp = new Date('2025-11-07T12:00:00Z').toISOString();
    expect(formatTimestamp(timestamp)).toBe('1 day ago');
  });

  it('should format as date for timestamps older than 7 days', () => {
    const timestamp = new Date('2025-11-01T12:00:00Z').toISOString();
    const result = formatTimestamp(timestamp);
    // The exact format depends on locale, so just check it's a date string
    expect(result).toMatch(/\d+\/\d+\/\d+/);
  });
});

describe('formatCurrency', () => {
  it('should format platinum pieces', () => {
    const currency: CurrencyValues = { platinum: 5, gold: 0, silver: 0, copper: 0 };
    expect(formatCurrency(currency)).toBe('5 pp');
  });

  it('should format gold pieces', () => {
    const currency: CurrencyValues = { platinum: 0, gold: 10, silver: 0, copper: 0 };
    expect(formatCurrency(currency)).toBe('10 gp');
  });

  it('should format silver pieces', () => {
    const currency: CurrencyValues = { platinum: 0, gold: 0, silver: 25, copper: 0 };
    expect(formatCurrency(currency)).toBe('25 sp');
  });

  it('should format copper pieces', () => {
    const currency: CurrencyValues = { platinum: 0, gold: 0, silver: 0, copper: 50 };
    expect(formatCurrency(currency)).toBe('50 cp');
  });

  it('should format multiple currency types', () => {
    const currency: CurrencyValues = { platinum: 1, gold: 10, silver: 5, copper: 3 };
    expect(formatCurrency(currency)).toBe('1 pp, 10 gp, 5 sp, 3 cp');
  });

  it('should omit zero values', () => {
    const currency: CurrencyValues = { platinum: 0, gold: 10, silver: 0, copper: 5 };
    expect(formatCurrency(currency)).toBe('10 gp, 5 cp');
  });

  it('should return "0 cp" for all zeros', () => {
    const currency: CurrencyValues = { platinum: 0, gold: 0, silver: 0, copper: 0 };
    expect(formatCurrency(currency)).toBe('0 cp');
  });
});

describe('formatModifier', () => {
  it('should format positive modifiers with + sign', () => {
    expect(formatModifier(3)).toBe('+3');
    expect(formatModifier(1)).toBe('+1');
  });

  it('should format zero with + sign', () => {
    expect(formatModifier(0)).toBe('+0');
  });

  it('should format negative modifiers', () => {
    expect(formatModifier(-1)).toBe('-1');
    expect(formatModifier(-5)).toBe('-5');
  });
});

describe('formatDiceNotation', () => {
  it('should format basic dice notation without modifier', () => {
    expect(formatDiceNotation(1, 20, 0)).toBe('1d20');
    expect(formatDiceNotation(2, 6, 0)).toBe('2d6');
  });

  it('should format dice notation with positive modifier', () => {
    expect(formatDiceNotation(1, 20, 5)).toBe('1d20+5');
    expect(formatDiceNotation(2, 6, 3)).toBe('2d6+3');
  });

  it('should format dice notation with negative modifier', () => {
    expect(formatDiceNotation(1, 20, -2)).toBe('1d20-2');
    expect(formatDiceNotation(3, 8, -1)).toBe('3d8-1');
  });

  it('should omit modifier when not provided', () => {
    expect(formatDiceNotation(1, 20)).toBe('1d20');
  });
});

describe('formatHitPoints', () => {
  it('should format current and max HP', () => {
    expect(formatHitPoints(45, 50)).toBe('45/50');
  });

  it('should format HP with temporary HP', () => {
    expect(formatHitPoints(45, 50, 5)).toBe('45/50 (+5)');
  });

  it('should handle zero current HP', () => {
    expect(formatHitPoints(0, 50)).toBe('0/50');
  });

  it('should handle zero temporary HP', () => {
    expect(formatHitPoints(45, 50, 0)).toBe('45/50');
  });

  it('should omit temporary HP when not provided', () => {
    expect(formatHitPoints(30, 40)).toBe('30/40');
  });
});

describe('formatAbilityScore', () => {
  it('should format ability score with positive modifier', () => {
    expect(formatAbilityScore(16)).toBe('16 (+3)');
    expect(formatAbilityScore(20)).toBe('20 (+5)');
  });

  it('should format ability score with zero modifier', () => {
    expect(formatAbilityScore(10)).toBe('10 (+0)');
    expect(formatAbilityScore(11)).toBe('11 (+0)');
  });

  it('should format ability score with negative modifier', () => {
    expect(formatAbilityScore(8)).toBe('8 (-1)');
    expect(formatAbilityScore(6)).toBe('6 (-2)');
  });

  it('should calculate modifier correctly for edge cases', () => {
    expect(formatAbilityScore(1)).toBe('1 (-5)');
    expect(formatAbilityScore(30)).toBe('30 (+10)');
  });
});

describe('formatOrdinal', () => {
  it('should format 1st, 2nd, 3rd', () => {
    expect(formatOrdinal(1)).toBe('1st');
    expect(formatOrdinal(2)).toBe('2nd');
    expect(formatOrdinal(3)).toBe('3rd');
  });

  it('should format 4th-10th', () => {
    expect(formatOrdinal(4)).toBe('4th');
    expect(formatOrdinal(10)).toBe('10th');
  });

  it('should handle 11th, 12th, 13th (special cases)', () => {
    expect(formatOrdinal(11)).toBe('11th');
    expect(formatOrdinal(12)).toBe('12th');
    expect(formatOrdinal(13)).toBe('13th');
  });

  it('should format 21st, 22nd, 23rd', () => {
    expect(formatOrdinal(21)).toBe('21st');
    expect(formatOrdinal(22)).toBe('22nd');
    expect(formatOrdinal(23)).toBe('23rd');
  });

  it('should format large numbers', () => {
    expect(formatOrdinal(101)).toBe('101st');
    expect(formatOrdinal(112)).toBe('112th');
    expect(formatOrdinal(1001)).toBe('1001st');
  });
});

describe('formatNumberAbbreviated', () => {
  it('should not abbreviate numbers less than 1000', () => {
    expect(formatNumberAbbreviated(999)).toBe('999');
    expect(formatNumberAbbreviated(0)).toBe('0');
  });

  it('should abbreviate thousands with K', () => {
    expect(formatNumberAbbreviated(1000)).toBe('1.0K');
    expect(formatNumberAbbreviated(1234)).toBe('1.2K');
    expect(formatNumberAbbreviated(999999)).toBe('1000.0K');
  });

  it('should abbreviate millions with M', () => {
    expect(formatNumberAbbreviated(1000000)).toBe('1.0M');
    expect(formatNumberAbbreviated(1234567)).toBe('1.2M');
  });

  it('should abbreviate billions with B', () => {
    expect(formatNumberAbbreviated(1000000000)).toBe('1.0B');
    expect(formatNumberAbbreviated(1234567890)).toBe('1.2B');
  });

  it('should respect decimals parameter', () => {
    expect(formatNumberAbbreviated(1234, 0)).toBe('1K');
    expect(formatNumberAbbreviated(1234, 2)).toBe('1.23K');
  });
});

describe('formatDistance', () => {
  it('should format distance in feet', () => {
    expect(formatDistance(30)).toBe('30 ft.');
    expect(formatDistance(120)).toBe('120 ft.');
    expect(formatDistance(5)).toBe('5 ft.');
  });
});

describe('formatWeight', () => {
  it('should format weight in pounds', () => {
    expect(formatWeight(15)).toBe('15 lb.');
    expect(formatWeight(0.5)).toBe('0.5 lb.');
    expect(formatWeight(100)).toBe('100 lb.');
  });
});

describe('formatDuration', () => {
  it('should format rounds (less than 10)', () => {
    expect(formatDuration(1)).toBe('1 round');
    expect(formatDuration(5)).toBe('5 rounds');
    expect(formatDuration(9)).toBe('9 rounds');
  });

  it('should format minutes (10-599 rounds)', () => {
    expect(formatDuration(10)).toBe('1 minute');
    expect(formatDuration(50)).toBe('5 minutes');
    expect(formatDuration(100)).toBe('10 minutes');
  });

  it('should format hours (600+ rounds)', () => {
    expect(formatDuration(600)).toBe('1 hour');
    expect(formatDuration(1200)).toBe('2 hours');
  });
});

describe('formatSpellLevel', () => {
  it('should format cantrip (level 0)', () => {
    expect(formatSpellLevel(0)).toBe('Cantrip');
  });

  it('should format 1st-level spell', () => {
    expect(formatSpellLevel(1)).toBe('1st-level');
  });

  it('should format 2nd-level spell', () => {
    expect(formatSpellLevel(2)).toBe('2nd-level');
  });

  it('should format 3rd-level spell', () => {
    expect(formatSpellLevel(3)).toBe('3rd-level');
  });

  it('should format 4th-9th level spells', () => {
    expect(formatSpellLevel(4)).toBe('4th-level');
    expect(formatSpellLevel(5)).toBe('5th-level');
    expect(formatSpellLevel(9)).toBe('9th-level');
  });
});

describe('formatProficiencyBonus', () => {
  it('should calculate proficiency bonus for level 1-4', () => {
    expect(formatProficiencyBonus(1)).toBe('+2');
    expect(formatProficiencyBonus(4)).toBe('+2');
  });

  it('should calculate proficiency bonus for level 5-8', () => {
    expect(formatProficiencyBonus(5)).toBe('+3');
    expect(formatProficiencyBonus(8)).toBe('+3');
  });

  it('should calculate proficiency bonus for level 9-12', () => {
    expect(formatProficiencyBonus(9)).toBe('+4');
    expect(formatProficiencyBonus(12)).toBe('+4');
  });

  it('should calculate proficiency bonus for level 13-16', () => {
    expect(formatProficiencyBonus(13)).toBe('+5');
    expect(formatProficiencyBonus(16)).toBe('+5');
  });

  it('should calculate proficiency bonus for level 17-20', () => {
    expect(formatProficiencyBonus(17)).toBe('+6');
    expect(formatProficiencyBonus(20)).toBe('+6');
  });
});

describe('pluralize', () => {
  it('should return singular for count of 1', () => {
    expect(pluralize(1, 'item')).toBe('1 item');
    expect(pluralize(1, 'party')).toBe('1 party');
  });

  it('should return plural for count greater than 1', () => {
    expect(pluralize(2, 'item')).toBe('2 items');
    expect(pluralize(5, 'item')).toBe('5 items');
  });

  it('should return plural for count of 0', () => {
    expect(pluralize(0, 'item')).toBe('0 items');
  });

  it('should use custom plural form', () => {
    expect(pluralize(2, 'party', 'parties')).toBe('2 parties');
    expect(pluralize(3, 'child', 'children')).toBe('3 children');
  });

  it('should use singular with custom plural when count is 1', () => {
    expect(pluralize(1, 'party', 'parties')).toBe('1 party');
  });
});
