/**
 * SkillsSection Component
 *
 * Displays all skills with modifiers and proficiency indicators.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { Character } from '../../types/generated/GameState.js';

export interface SkillsSectionProps {
  character: Character;
}

/**
 * Calculate ability modifier from ability score
 */
function calculateModifier(score: number): number {
  return Math.floor((score - 10) / 2);
}

/**
 * Format modifier with sign
 */
function formatModifier(modifier: number): string {
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
}

/**
 * Skill definitions with their governing abilities
 */
const SKILL_DEFINITIONS: Array<{ key: string; label: string; ability: keyof Character['abilities'] }> = [
  { key: 'acrobatics', label: 'Acrobatics', ability: 'dexterity' },
  { key: 'animal_handling', label: 'Animal Handling', ability: 'wisdom' },
  { key: 'arcana', label: 'Arcana', ability: 'intelligence' },
  { key: 'athletics', label: 'Athletics', ability: 'strength' },
  { key: 'deception', label: 'Deception', ability: 'charisma' },
  { key: 'history', label: 'History', ability: 'intelligence' },
  { key: 'insight', label: 'Insight', ability: 'wisdom' },
  { key: 'intimidation', label: 'Intimidation', ability: 'charisma' },
  { key: 'investigation', label: 'Investigation', ability: 'intelligence' },
  { key: 'medicine', label: 'Medicine', ability: 'wisdom' },
  { key: 'nature', label: 'Nature', ability: 'intelligence' },
  { key: 'perception', label: 'Perception', ability: 'wisdom' },
  { key: 'performance', label: 'Performance', ability: 'charisma' },
  { key: 'persuasion', label: 'Persuasion', ability: 'charisma' },
  { key: 'religion', label: 'Religion', ability: 'intelligence' },
  { key: 'sleight_of_hand', label: 'Sleight of Hand', ability: 'dexterity' },
  { key: 'stealth', label: 'Stealth', ability: 'dexterity' },
  { key: 'survival', label: 'Survival', ability: 'wisdom' },
];

/**
 * Skills section component
 */
export class SkillsSection extends Component<SkillsSectionProps> {
  constructor(props: SkillsSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'skills-section' });

    const header = div({ class: 'skills-section__header' }, 'Skills');
    container.appendChild(header);

    const skillsList = div({ class: 'skills-list' });

    for (const skill of SKILL_DEFINITIONS) {
      const abilityScore = this.props.character.abilities[skill.ability];
      const baseModifier = calculateModifier(abilityScore);
      const skillBonus = this.props.character.skills[skill.key] ?? baseModifier;
      const isProficient = skillBonus !== baseModifier;

      const skillRow = div({ class: 'skill-row' });

      // Proficiency indicator
      const profIndicator = div({
        class: `skill-row__proficiency ${isProficient ? 'skill-row__proficiency--active' : ''}`,
      });

      // Skill label
      const label = div({ class: 'skill-row__label' }, skill.label);

      // Skill bonus
      const bonus = div(
        { class: 'skill-row__bonus' },
        formatModifier(skillBonus)
      );

      skillRow.appendChild(profIndicator);
      skillRow.appendChild(label);
      skillRow.appendChild(bonus);

      skillsList.appendChild(skillRow);
    }

    container.appendChild(skillsList);

    return container;
  }
}
