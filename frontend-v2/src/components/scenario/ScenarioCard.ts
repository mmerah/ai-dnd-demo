/**
 * ScenarioCard Component
 *
 * Displays a selectable scenario card with basic information.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { Scenario } from '../../services/api/CatalogApiService.js';

export interface ScenarioCardProps {
  scenario: Scenario;
  isSelected: boolean;
  onSelect: (scenarioId: string) => void;
}

/**
 * Scenario card component for scenario selection
 */
export class ScenarioCard extends Component<ScenarioCardProps> {
  constructor(props: ScenarioCardProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { scenario, isSelected } = this.props;

    const card = div({
      class: `scenario-card ${isSelected ? 'scenario-card--selected' : ''}`,
      onclick: () => this.handleSelect(),
    });

    // Scenario title
    const title = div({ class: 'scenario-card__title' }, scenario.name);

    // Scenario description preview
    const description = div({ class: 'scenario-card__description' });
    description.textContent = this.truncateDescription(scenario.description);

    // Difficulty badge (if available)
    if (scenario.difficulty) {
      const difficulty = div({ class: 'scenario-card__difficulty' });
      const badge = div(
        {
          class: `scenario-card__difficulty-badge scenario-card__difficulty-badge--${scenario.difficulty.toLowerCase()}`,
        },
        scenario.difficulty
      );
      difficulty.appendChild(badge);
      card.appendChild(difficulty);
    }

    // Selection indicator
    if (isSelected) {
      const indicator = div({ class: 'scenario-card__indicator' }, '✓');
      card.appendChild(indicator);
    }

    card.appendChild(title);
    card.appendChild(description);

    return card;
  }

  override onUpdate(prevProps: ScenarioCardProps): void {
    // Re-render if selection state changed
    if (prevProps.isSelected !== this.props.isSelected) {
      this.rerender();
    }
  }

  private handleSelect(): void {
    this.props.onSelect(this.props.scenario.id);
  }

  private truncateDescription(description: string, maxLength: number = 120): string {
    if (description.length <= maxLength) {
      return description;
    }
    return description.substring(0, maxLength).trim() + '...';
  }

  private rerender(): void {
    if (!this.element || !this.element.parentElement) return;

    const parent = this.element.parentElement;
    this.unmount();
    this.mount(parent);
  }
}
