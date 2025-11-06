/**
 * AbilitiesSection Component
 *
 * Displays the six ability scores with modifiers and saving throw bonuses.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance } from '../../types/generated/GameState.js';

export interface AbilitiesSectionProps {
  character: CharacterInstance;
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
 * Abilities section component
 */
export class AbilitiesSection extends Component<AbilitiesSectionProps> {
  constructor(props: AbilitiesSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'abilities-section' });

    const abilities: Array<{ key: 'STR' | 'DEX' | 'CON' | 'INT' | 'WIS' | 'CHA'; label: string }> = [
      { key: 'STR', label: 'STR' },
      { key: 'DEX', label: 'DEX' },
      { key: 'CON', label: 'CON' },
      { key: 'INT', label: 'INT' },
      { key: 'WIS', label: 'WIS' },
      { key: 'CHA', label: 'CHA' },
    ];

    const grid = div({ class: 'abilities-grid' });

    for (const ability of abilities) {
      const score = this.props.character.state.abilities[ability.key];
      const modifier = calculateModifier(score);
      const savingThrowKey = ability.key;
      const savingThrow = this.props.character.state.saving_throws?.[savingThrowKey] ?? modifier;
      const isProficient = savingThrow !== modifier;

      const abilityCard = div({ class: 'ability-card' });

      // Label
      const label = div({ class: 'ability-card__label' }, ability.label);

      // Score (large)
      const scoreValue = div({ class: 'ability-card__score' }, score.toString());

      // Modifier
      const modifierValue = div(
        { class: 'ability-card__modifier' },
        formatModifier(modifier)
      );

      // Saving throw
      const savingThrowContainer = div({ class: 'ability-card__saving-throw' });
      const proficiencyIndicator = div({
        class: `ability-card__proficiency ${isProficient ? 'ability-card__proficiency--active' : ''}`,
      });
      const savingThrowLabel = div(
        { class: 'ability-card__saving-throw-label' },
        'Save'
      );
      const savingThrowValue = div(
        { class: 'ability-card__saving-throw-value' },
        formatModifier(savingThrow)
      );

      savingThrowContainer.appendChild(proficiencyIndicator);
      savingThrowContainer.appendChild(savingThrowLabel);
      savingThrowContainer.appendChild(savingThrowValue);

      // Assemble card
      abilityCard.appendChild(label);
      abilityCard.appendChild(scoreValue);
      abilityCard.appendChild(modifierValue);
      abilityCard.appendChild(savingThrowContainer);

      grid.appendChild(abilityCard);
    }

    container.appendChild(grid);

    return container;
  }
}
