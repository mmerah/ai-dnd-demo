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
  conditions: string[];
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

    // Status indicator
    const statusIndicator = this.createStatusIndicator(member.hp, member.max_hp, member.conditions);
    card.appendChild(statusIndicator);

    // Conditions display (if any)
    if (member.conditions.length > 0) {
      const conditionsDisplay = this.createConditionsDisplay(member.conditions);
      card.appendChild(conditionsDisplay);
    }

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

  private createStatusIndicator(hp: number, maxHp: number, conditions: string[]): HTMLElement {
    const container = div({ class: 'party-member-card__status' });

    const statusInfo = this.getStatusInfo(hp, maxHp, conditions);

    const iconEl = span({ class: `party-member-card__status-icon party-member-card__status-icon--${statusInfo.class}` });
    iconEl.textContent = statusInfo.icon;

    const textEl = span({ class: 'party-member-card__status-text' });
    textEl.textContent = statusInfo.text;

    container.appendChild(iconEl);
    container.appendChild(textEl);

    return container;
  }

  private createConditionsDisplay(conditions: string[]): HTMLElement {
    const container = div({ class: 'party-member-card__conditions' });

    for (const condition of conditions) {
      const badge = div({ class: 'party-member-card__condition-badge' });
      badge.textContent = condition;
      container.appendChild(badge);
    }

    return container;
  }

  private getStatusInfo(hp: number, maxHp: number, conditions: string[]): { icon: string; text: string; class: string } {
    const hpPercent = maxHp > 0 ? (hp / maxHp) * 100 : 0;

    // Check for death/unconsciousness
    if (hp <= 0) {
      const isDead = conditions.some(c => c.toLowerCase() === 'dead');
      if (isDead) {
        return { icon: '💀', text: 'Dead', class: 'dead' };
      }
      return { icon: '💤', text: 'Unconscious', class: 'unconscious' };
    }

    // Health status based on HP percentage
    if (hpPercent >= 75) {
      return { icon: '🟢', text: 'Healthy', class: 'healthy' };
    } else if (hpPercent >= 30) {
      return { icon: '🟡', text: 'Wounded', class: 'wounded' };
    } else {
      return { icon: '🔴', text: 'Critical', class: 'critical' };
    }
  }
}
