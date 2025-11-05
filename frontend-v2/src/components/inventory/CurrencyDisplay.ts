/**
 * CurrencyDisplay Component
 *
 * Displays character currency (copper, silver, gold, platinum).
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';

export interface CurrencyDisplayProps {
  // Currency will be added to Character type in the future
  copper?: number;
  silver?: number;
  electrum?: number;
  gold?: number;
  platinum?: number;
}

/**
 * Currency display component
 */
export class CurrencyDisplay extends Component<CurrencyDisplayProps> {
  constructor(props: CurrencyDisplayProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'currency-display' });

    const header = div({ class: 'currency-display__header' }, 'Currency');
    container.appendChild(header);

    const currencies = [
      { key: 'platinum' as const, label: 'Platinum', abbr: 'pp', value: this.props.platinum ?? 0 },
      { key: 'gold' as const, label: 'Gold', abbr: 'gp', value: this.props.gold ?? 0 },
      { key: 'electrum' as const, label: 'Electrum', abbr: 'ep', value: this.props.electrum ?? 0 },
      { key: 'silver' as const, label: 'Silver', abbr: 'sp', value: this.props.silver ?? 0 },
      { key: 'copper' as const, label: 'Copper', abbr: 'cp', value: this.props.copper ?? 0 },
    ];

    const hasCurrency = currencies.some(c => c.value > 0);

    if (hasCurrency) {
      const grid = div({ class: 'currency-grid' });

      for (const currency of currencies) {
        const currencyItem = div({ class: 'currency-item' });

        const label = div({ class: 'currency-item__label' }, currency.abbr);
        const value = div(
          { class: 'currency-item__value' },
          currency.value.toLocaleString()
        );

        currencyItem.appendChild(label);
        currencyItem.appendChild(value);

        grid.appendChild(currencyItem);
      }

      container.appendChild(grid);
    } else {
      const placeholder = div(
        { class: 'currency-display__empty' },
        'No currency to display. Currency tracking will be available when added to the backend.'
      );
      container.appendChild(placeholder);
    }

    return container;
  }
}
