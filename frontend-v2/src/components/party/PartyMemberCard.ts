/**
 * PartyMemberCard component
 *
 * Displays a single party member's status card with HP, AC, level, and class.
 * Supports selection highlighting.
 */

import { Component } from '../base/Component.js';
import { createElement, div, span } from '../../utils/dom.js';

interface PartyMember {
  id: string;
  name: string;
  role: string;
  hp: number;
  max_hp: number;
  ac: number | undefined;
  level: number | undefined;
  class_name: string;
}

export interface PartyMemberCardProps {
  member: PartyMember;
  isSelected: boolean;
  onSelect: (memberId: string) => void;
}

export class PartyMemberCard extends Component<PartyMemberCardProps> {
  protected render(): HTMLElement {
    const { member, isSelected, onSelect } = this.props;

    const card = div({
      class: `party-member-card ${isSelected ? 'party-member-card--selected' : ''}`,
      'data-member-id': member.id,
      'data-role': member.role,
      onClick: () => onSelect(member.id),
    });

    // Header with name and role
    const header = div({ class: 'party-member-card__header' });
    const name = createElement('h3', { class: 'party-member-card__name' });
    name.textContent = member.name;

    const role = span({ class: 'party-member-card__role' });
    role.textContent = member.role === 'player' ? 'Player' : 'Companion';

    header.appendChild(name);
    header.appendChild(role);

    // Stats grid
    const stats = div({ class: 'party-member-card__stats' });

    // HP bar
    const hpBar = this.createStatBar('HP', member.hp, member.max_hp);

    // Other stats
    const otherStats = div({ class: 'party-member-card__stat-grid' });
    otherStats.appendChild(this.createStatItem('AC', (member.ac ?? 10).toString()));
    otherStats.appendChild(this.createStatItem('Level', (member.level ?? 1).toString()));
    otherStats.appendChild(this.createStatItem('Class', member.class_name));

    stats.appendChild(hpBar);
    stats.appendChild(otherStats);

    card.appendChild(header);
    card.appendChild(stats);

    return card;
  }

  private createStatBar(label: string, current: number, max: number): HTMLElement {
    const container = div({ class: 'stat-bar' });

    const labelEl = span({ class: 'stat-bar__label' });
    labelEl.textContent = label;

    const valuesEl = span({ class: 'stat-bar__values' });
    valuesEl.textContent = `${current} / ${max}`;

    const barContainer = div({ class: 'stat-bar__bar-container' });
    const barFill = div({
      class: `stat-bar__bar-fill ${this.getHPColorClass(current, max)}`,
    });

    const percentage = Math.max(0, Math.min(100, (current / max) * 100));
    (barFill as HTMLElement).style.width = `${percentage}%`;

    barContainer.appendChild(barFill);

    const topRow = div({ class: 'stat-bar__top' });
    topRow.appendChild(labelEl);
    topRow.appendChild(valuesEl);

    container.appendChild(topRow);
    container.appendChild(barContainer);

    return container;
  }

  private createStatItem(label: string, value: string): HTMLElement {
    const item = div({ class: 'stat-item' });

    const labelEl = span({ class: 'stat-item__label' });
    labelEl.textContent = label;

    const valueEl = span({ class: 'stat-item__value' });
    valueEl.textContent = value;

    item.appendChild(labelEl);
    item.appendChild(valueEl);

    return item;
  }

  private getHPColorClass(current: number, max: number): string {
    const percentage = (current / max) * 100;

    if (percentage > 75) return 'stat-bar__bar-fill--high';
    if (percentage > 25) return 'stat-bar__bar-fill--medium';
    return 'stat-bar__bar-fill--low';
  }
}
