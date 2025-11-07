/**
 * FeaturesSection Component
 *
 * Displays character features including proficiency bonus and conditions.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance } from '../../types/generated/GameState.js';

export interface FeaturesSectionProps {
  character: CharacterInstance;
  initiallyCollapsed?: boolean;
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
  private collapsibleSection: CollapsibleSection | null = null;

  constructor(props: FeaturesSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const content = div({ class: 'features-section__content' });

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
    content.appendChild(proficiencyRow);

    // Active conditions
    const conditions = this.props.character.state.conditions ?? [];
    if (conditions.length > 0) {
      const conditionsHeader = div({ class: 'features-section__subheader' }, 'Active Conditions');
      content.appendChild(conditionsHeader);

      const conditionsList = div({ class: 'conditions-list' });
      for (const condition of conditions) {
        const conditionBadge = div(
          { class: 'condition-badge' },
          condition
        );
        conditionsList.appendChild(conditionBadge);
      }
      content.appendChild(conditionsList);
    }

    // Placeholder for future features
    const placeholderText = div(
      { class: 'features-section__placeholder' },
      'Racial traits and class features will be displayed here when available from the backend.'
    );
    content.appendChild(placeholderText);

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Features & Traits',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [content],
    });

    const container = div({ class: 'features-section' });
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
