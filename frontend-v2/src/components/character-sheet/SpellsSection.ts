/**
 * SpellsSection Component
 *
 * Displays spell slots and known spells.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance, SpellSlot } from '../../types/generated/GameState.js';

export interface SpellsSectionProps {
  character: CharacterInstance;
}

/**
 * Spells section component
 */
export class SpellsSection extends Component<SpellsSectionProps> {
  constructor(props: SpellsSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'spells-section' });

    const header = div({ class: 'spells-section__header' }, 'Spellcasting');
    container.appendChild(header);

    const spellcasting = this.props.character.state.spellcasting;

    // Check if character has spellcasting
    if (!spellcasting) {
      const noSpells = div(
        { class: 'spells-section__empty' },
        'This character does not have spellcasting abilities.'
      );
      container.appendChild(noSpells);
      return container;
    }

    // Spell slots
    const spellSlots = Object.entries(spellcasting.spell_slots ?? {});
    if (spellSlots.length > 0) {
      const slotsHeader = div({ class: 'spells-section__subheader' }, 'Spell Slots');
      container.appendChild(slotsHeader);

      const slotsGrid = div({ class: 'spell-slots-grid' });

      // Sort by level
      spellSlots.sort((a, b) => {
        const levelA = (a[1] as SpellSlot).level;
        const levelB = (b[1] as SpellSlot).level;
        return levelA - levelB;
      });

      for (const [, slot] of spellSlots) {
        const slotCard = this.renderSpellSlot(slot as SpellSlot);
        slotsGrid.appendChild(slotCard);
      }

      container.appendChild(slotsGrid);
    }

    // Known spells
    const knownSpells = spellcasting.spells_known ?? [];
    if (knownSpells.length > 0) {
      const spellsHeader = div({ class: 'spells-section__subheader' }, 'Known Spells');
      container.appendChild(spellsHeader);

      const spellsList = div({ class: 'known-spells-list' });
      for (const spell of knownSpells) {
        const spellItem = div({ class: 'spell-item' }, spell);
        spellsList.appendChild(spellItem);
      }
      container.appendChild(spellsList);
    }

    return container;
  }

  private renderSpellSlot(slot: SpellSlot): HTMLElement {
    const card = div({ class: 'spell-slot-card' });

    // Level label
    const levelLabel = div(
      { class: 'spell-slot-card__level' },
      `Level ${slot.level}`
    );

    // Slot usage
    const available = slot.total - slot.current;
    const usageContainer = div({ class: 'spell-slot-card__usage' });

    // Visual slot indicators
    const slotsVisual = div({ class: 'spell-slot-card__slots' });
    const total = slot.total;
    for (let i = 0; i < total; i++) {
      const slotDot = div({
        class: `spell-slot-dot ${i < available ? 'spell-slot-dot--available' : 'spell-slot-dot--used'}`,
      });
      slotsVisual.appendChild(slotDot);
    }

    // Text indicator
    const usageText = div(
      { class: 'spell-slot-card__text' },
      `${available} / ${total}`
    );

    usageContainer.appendChild(slotsVisual);
    usageContainer.appendChild(usageText);

    card.appendChild(levelLabel);
    card.appendChild(usageContainer);

    return card;
  }
}
