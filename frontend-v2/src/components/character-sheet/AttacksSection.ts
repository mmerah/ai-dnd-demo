/**
 * AttacksSection Component
 *
 * Displays character attacks with attack bonuses, damage, and properties.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance, AttackAction } from '../../types/generated/GameState.js';

export interface AttacksSectionProps {
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
 * Attacks section component
 */
export class AttacksSection extends Component<AttacksSectionProps> {
  private collapsibleSection: CollapsibleSection | null = null;

  constructor(props: AttacksSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const content = div({ class: 'attacks-section__content' });

    const attacks = this.props.character.state.attacks ?? [];

    // Check if character has attacks
    if (attacks.length === 0) {
      const noAttacks = div(
        { class: 'attacks-section__empty' },
        'No attacks available'
      );
      content.appendChild(noAttacks);
    } else {
      const attacksList = div({ class: 'attacks-list' });

      for (const attack of attacks) {
        const attackItem = this.renderAttackItem(attack);
        attacksList.appendChild(attackItem);
      }

      content.appendChild(attacksList);
    }

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Attacks',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [content],
    });

    const container = div({ class: 'attacks-section' });
    this.collapsibleSection.mount(container);

    return container;
  }

  override onUnmount(): void {
    if (this.collapsibleSection) {
      this.collapsibleSection.unmount();
      this.collapsibleSection = null;
    }
  }

  private renderAttackItem(attack: AttackAction): HTMLElement {
    const row = div({ class: 'attack-item' });

    // Left side: attack name
    const left = div({ class: 'attack-name' }, attack.name || 'Unknown');

    // Right side: attack metadata
    const right = div({ class: 'attack-meta' });

    // Build metadata parts
    const parts: string[] = [];

    // Attack roll bonus
    if (typeof attack.attack_roll_bonus === 'number') {
      const toHitVal = formatModifier(attack.attack_roll_bonus);
      parts.push(`Attack Roll ${toHitVal}`);
    }

    // Damage
    if (attack.damage) {
      const damageType = attack.damage_type
        ? ` ${attack.damage_type.toLowerCase()}`
        : '';
      parts.push(`Damage ${attack.damage}${damageType}`);
    }

    // Range
    if (attack.range) {
      parts.push(attack.range);
    }

    right.textContent = parts.join(' • ');

    row.appendChild(left);
    row.appendChild(right);

    return row;
  }
}
