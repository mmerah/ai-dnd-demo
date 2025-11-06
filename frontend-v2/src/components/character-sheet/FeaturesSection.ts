/**
 * FeaturesSection Component
 *
 * Displays character features including proficiency bonus and conditions.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance } from '../../types/generated/GameState.js';

export interface FeaturesSectionProps {
  character: CharacterInstance;
}

/**
 * Format modifier with sign
 */
function formatModifier(modifier: number): string {
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
}

/**
 * Features section component
 */
export class FeaturesSection extends Component<FeaturesSectionProps> {
  constructor(props: FeaturesSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'features-section' });

    const header = div({ class: 'features-section__header' }, 'Features & Traits');
    container.appendChild(header);

    // Proficiency bonus - calculate from level
    const level = this.props.character.state.level ?? 1;
    const proficiencyBonus = Math.ceil(level / 4) + 1;
    const proficiencyRow = div({ class: 'feature-row' });
    const profLabel = div({ class: 'feature-row__label' }, 'Proficiency Bonus');
    const profValue = div(
      { class: 'feature-row__value' },
      formatModifier(proficiencyBonus)
    );
    proficiencyRow.appendChild(profLabel);
    proficiencyRow.appendChild(profValue);
    container.appendChild(proficiencyRow);

    // Active conditions
    const conditions = this.props.character.state.conditions ?? [];
    if (conditions.length > 0) {
      const conditionsHeader = div({ class: 'features-section__subheader' }, 'Active Conditions');
      container.appendChild(conditionsHeader);

      const conditionsList = div({ class: 'conditions-list' });
      for (const condition of conditions) {
        const conditionBadge = div(
          { class: 'condition-badge' },
          condition
        );
        conditionsList.appendChild(conditionBadge);
      }
      container.appendChild(conditionsList);
    }

    // Placeholder for future features
    const placeholderText = div(
      { class: 'features-section__placeholder' },
      'Racial traits and class features will be displayed here when available from the backend.'
    );
    container.appendChild(placeholderText);

    return container;
  }
}
