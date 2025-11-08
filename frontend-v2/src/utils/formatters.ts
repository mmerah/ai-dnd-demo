/**
 * Formatting Utilities
 *
 * Pure functions for formatting data into display-friendly strings.
 * Extracted from components to follow DRY principle.
 *
 * All formatters are pure functions with no side effects.
 */

/**
 * Formats an ISO timestamp into a relative time string
 * @param isoString - ISO 8601 timestamp string
 * @returns Relative time string (e.g., "2 hours ago", "just now")
 * @example
 * ```ts
 * formatTimestamp('2025-11-08T10:00:00Z') // "2 hours ago"
 * formatTimestamp('2025-11-08T11:58:00Z') // "2 minutes ago"
 * ```
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 10) {
    return 'just now';
  } else if (diffSec < 60) {
    return `${diffSec} ${diffSec === 1 ? 'second' : 'seconds'} ago`;
  } else if (diffMin < 60) {
    return `${diffMin} ${diffMin === 1 ? 'minute' : 'minutes'} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} ${diffHour === 1 ? 'hour' : 'hours'} ago`;
  } else if (diffDay < 7) {
    return `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`;
  } else {
    // For dates older than 7 days, show the actual date
    return date.toLocaleDateString();
  }
}

/**
 * Currency values in copper pieces
 */
export interface CurrencyValues {
  /** Copper pieces */
  copper: number;
  /** Silver pieces */
  silver: number;
  /** Gold pieces */
  gold: number;
  /** Platinum pieces */
  platinum: number;
}

/**
 * Formats currency values into a readable string
 * @param currency - Currency values (cp, sp, gp, pp)
 * @returns Formatted currency string (e.g., "10 gp, 5 sp, 3 cp")
 * @example
 * ```ts
 * formatCurrency({ copper: 3, silver: 5, gold: 10, platinum: 0 })
 * // "10 gp, 5 sp, 3 cp"
 *
 * formatCurrency({ copper: 0, silver: 0, gold: 0, platinum: 1 })
 * // "1 pp"
 * ```
 */
export function formatCurrency(currency: CurrencyValues): string {
  const parts: string[] = [];

  if (currency.platinum > 0) {
    parts.push(`${currency.platinum} pp`);
  }
  if (currency.gold > 0) {
    parts.push(`${currency.gold} gp`);
  }
  if (currency.silver > 0) {
    parts.push(`${currency.silver} sp`);
  }
  if (currency.copper > 0) {
    parts.push(`${currency.copper} cp`);
  }

  if (parts.length === 0) {
    return '0 cp';
  }

  return parts.join(', ');
}

/**
 * Formats a numeric modifier with proper sign
 * @param value - Modifier value
 * @returns Formatted modifier string (e.g., "+3", "-1", "+0")
 * @example
 * ```ts
 * formatModifier(3)  // "+3"
 * formatModifier(-1) // "-1"
 * formatModifier(0)  // "+0"
 * ```
 */
export function formatModifier(value: number): string {
  if (value >= 0) {
    return `+${value}`;
  }
  return `${value}`;
}

/**
 * Formats dice notation with modifier
 * @param count - Number of dice
 * @param sides - Number of sides per die
 * @param modifier - Modifier to add (optional)
 * @returns Formatted dice notation (e.g., "2d6+3", "1d20")
 * @example
 * ```ts
 * formatDiceNotation(2, 6, 3)  // "2d6+3"
 * formatDiceNotation(1, 20, 0) // "1d20"
 * formatDiceNotation(3, 8, -2) // "3d8-2"
 * ```
 */
export function formatDiceNotation(count: number, sides: number, modifier: number = 0): string {
  const base = `${count}d${sides}`;

  if (modifier === 0) {
    return base;
  }

  const modStr = modifier > 0 ? `+${modifier}` : `${modifier}`;
  return `${base}${modStr}`;
}

/**
 * Formats hit points with current, max, and temporary HP
 * @param current - Current HP
 * @param max - Maximum HP
 * @param temp - Temporary HP (optional)
 * @returns Formatted HP string (e.g., "45/50", "45/50 (+5)")
 * @example
 * ```ts
 * formatHitPoints(45, 50)     // "45/50"
 * formatHitPoints(45, 50, 5)  // "45/50 (+5)"
 * formatHitPoints(0, 50)      // "0/50"
 * ```
 */
export function formatHitPoints(current: number, max: number, temp: number = 0): string {
  const base = `${current}/${max}`;

  if (temp > 0) {
    return `${base} (+${temp})`;
  }

  return base;
}

/**
 * Formats ability score with modifier
 * @param score - Ability score (1-30)
 * @returns Formatted ability string (e.g., "16 (+3)")
 * @example
 * ```ts
 * formatAbilityScore(16) // "16 (+3)"
 * formatAbilityScore(8)  // "8 (-1)"
 * formatAbilityScore(10) // "10 (+0)"
 * ```
 */
export function formatAbilityScore(score: number): string {
  const modifier = Math.floor((score - 10) / 2);
  return `${score} (${formatModifier(modifier)})`;
}

/**
 * Formats a number with ordinal suffix
 * @param num - Number to format
 * @returns Number with ordinal suffix (e.g., "1st", "2nd", "3rd", "4th")
 * @example
 * ```ts
 * formatOrdinal(1)  // "1st"
 * formatOrdinal(2)  // "2nd"
 * formatOrdinal(3)  // "3rd"
 * formatOrdinal(11) // "11th"
 * formatOrdinal(21) // "21st"
 * ```
 */
export function formatOrdinal(num: number): string {
  const j = num % 10;
  const k = num % 100;

  if (j === 1 && k !== 11) {
    return `${num}st`;
  }
  if (j === 2 && k !== 12) {
    return `${num}nd`;
  }
  if (j === 3 && k !== 13) {
    return `${num}rd`;
  }
  return `${num}th`;
}

/**
 * Formats a large number with abbreviations (K, M, B)
 * @param num - Number to format
 * @param decimals - Number of decimal places (default: 1)
 * @returns Abbreviated number string (e.g., "1.2K", "3.4M")
 * @example
 * ```ts
 * formatNumberAbbreviated(1234)      // "1.2K"
 * formatNumberAbbreviated(1234567)   // "1.2M"
 * formatNumberAbbreviated(1234, 0)   // "1K"
 * ```
 */
export function formatNumberAbbreviated(num: number, decimals: number = 1): string {
  if (num < 1000) {
    return num.toString();
  } else if (num < 1000000) {
    return (num / 1000).toFixed(decimals) + 'K';
  } else if (num < 1000000000) {
    return (num / 1000000).toFixed(decimals) + 'M';
  } else {
    return (num / 1000000000).toFixed(decimals) + 'B';
  }
}

/**
 * Formats a distance in feet
 * @param feet - Distance in feet
 * @returns Formatted distance string (e.g., "30 ft.", "120 ft.")
 * @example
 * ```ts
 * formatDistance(30)  // "30 ft."
 * formatDistance(120) // "120 ft."
 * ```
 */
export function formatDistance(feet: number): string {
  return `${feet} ft.`;
}

/**
 * Formats a weight in pounds
 * @param pounds - Weight in pounds
 * @returns Formatted weight string (e.g., "15 lb.", "0.5 lb.")
 * @example
 * ```ts
 * formatWeight(15)  // "15 lb."
 * formatWeight(0.5) // "0.5 lb."
 * ```
 */
export function formatWeight(pounds: number): string {
  return `${pounds} lb.`;
}

/**
 * Formats a duration in rounds/minutes/hours
 * @param rounds - Duration in rounds (6 seconds per round)
 * @returns Formatted duration string
 * @example
 * ```ts
 * formatDuration(1)   // "1 round"
 * formatDuration(10)  // "1 minute"
 * formatDuration(100) // "10 minutes"
 * formatDuration(600) // "1 hour"
 * ```
 */
export function formatDuration(rounds: number): string {
  if (rounds < 10) {
    return `${rounds} ${rounds === 1 ? 'round' : 'rounds'}`;
  }

  const minutes = rounds / 10;
  if (minutes < 60) {
    return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`;
  }

  const hours = minutes / 60;
  return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
}

/**
 * Formats a spell level
 * @param level - Spell level (0-9)
 * @returns Formatted spell level string (e.g., "Cantrip", "1st-level", "2nd-level")
 * @example
 * ```ts
 * formatSpellLevel(0) // "Cantrip"
 * formatSpellLevel(1) // "1st-level"
 * formatSpellLevel(2) // "2nd-level"
 * formatSpellLevel(9) // "9th-level"
 * ```
 */
export function formatSpellLevel(level: number): string {
  if (level === 0) {
    return 'Cantrip';
  }
  return `${formatOrdinal(level)}-level`;
}

/**
 * Formats a proficiency bonus
 * @param level - Character level
 * @returns Formatted proficiency bonus (e.g., "+2", "+6")
 * @example
 * ```ts
 * formatProficiencyBonus(1)  // "+2"
 * formatProficiencyBonus(5)  // "+3"
 * formatProficiencyBonus(17) // "+6"
 * ```
 */
export function formatProficiencyBonus(level: number): string {
  const bonus = Math.ceil(level / 4) + 1;
  return formatModifier(bonus);
}

/**
 * Pluralizes a word based on count
 * @param count - Number of items
 * @param singular - Singular form of the word
 * @param plural - Plural form of the word (optional, defaults to singular + 's')
 * @returns Pluralized string with count
 * @example
 * ```ts
 * pluralize(1, 'item')       // "1 item"
 * pluralize(5, 'item')       // "5 items"
 * pluralize(2, 'party', 'parties') // "2 parties"
 * ```
 */
export function pluralize(count: number, singular: string, plural?: string): string {
  const word = count === 1 ? singular : plural || `${singular}s`;
  return `${count} ${word}`;
}
