/**
 * ScenarioCard Component
 *
 * Displays a selectable scenario card with basic information.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { ScenarioSheet } from '../../types/generated/ScenarioSheet.js';

export interface ScenarioCardProps {
  scenario: ScenarioSheet;
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
    const title = div({ class: 'scenario-card__title' }, scenario.title);

    // Scenario description preview
    const description = div({ class: 'scenario-card__description' });
    description.textContent = this.truncateDescription(scenario.description);

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
    // Backend always returns scenarios with ids, but type marks it optional
    const scenarioId = this.props.scenario.id;
    if (scenarioId) {
      this.props.onSelect(scenarioId);
    }
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
