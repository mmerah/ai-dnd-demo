/**
 * SkillsSection Component
 *
 * Displays all skills with modifiers and proficiency indicators.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance } from '../../types/generated/GameState.js';

export interface SkillsSectionProps {
  character: CharacterInstance;
  initiallyCollapsed?: boolean;
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
const SKILL_DEFINITIONS: Array<{ key: string; label: string; ability: 'STR' | 'DEX' | 'CON' | 'INT' | 'WIS' | 'CHA' }> = [
  { key: 'acrobatics', label: 'Acrobatics', ability: 'DEX' },
  { key: 'animal-handling', label: 'Animal Handling', ability: 'WIS' },
  { key: 'arcana', label: 'Arcana', ability: 'INT' },
  { key: 'athletics', label: 'Athletics', ability: 'STR' },
  { key: 'deception', label: 'Deception', ability: 'CHA' },
  { key: 'history', label: 'History', ability: 'INT' },
  { key: 'insight', label: 'Insight', ability: 'WIS' },
  { key: 'intimidation', label: 'Intimidation', ability: 'CHA' },
  { key: 'investigation', label: 'Investigation', ability: 'INT' },
  { key: 'medicine', label: 'Medicine', ability: 'WIS' },
  { key: 'nature', label: 'Nature', ability: 'INT' },
  { key: 'perception', label: 'Perception', ability: 'WIS' },
  { key: 'performance', label: 'Performance', ability: 'CHA' },
  { key: 'persuasion', label: 'Persuasion', ability: 'CHA' },
  { key: 'religion', label: 'Religion', ability: 'INT' },
  { key: 'sleight-of-hand', label: 'Sleight of Hand', ability: 'DEX' },
  { key: 'stealth', label: 'Stealth', ability: 'DEX' },
  { key: 'survival', label: 'Survival', ability: 'WIS' },
];

/**
 * Skills section component
 */
export class SkillsSection extends Component<SkillsSectionProps> {
  private collapsibleSection: CollapsibleSection | null = null;

  constructor(props: SkillsSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const skillsList = div({ class: 'skills-list' });

    for (const skill of SKILL_DEFINITIONS) {
      const abilityScore = this.props.character.state.abilities[skill.ability];
      const baseModifier = calculateModifier(abilityScore);
      const skillValue = this.props.character.state.skills?.find(s => s.index === skill.key);
      const skillBonus = skillValue?.value ?? baseModifier;
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

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Skills',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [skillsList],
    });

    const container = div({ class: 'skills-section' });
    this.collapsibleSection.mount(container);

    return container;
  }

  override onUnmount(): void {
    if (this.collapsibleSection) {
      this.collapsibleSection.unmount();
      this.collapsibleSection = null;
    }
  }
}
