/**
 * SpellsSection Component
 *
 * Displays spell slots and known spells.
 */

import { Component } from '../base/Component.js';
import { CollapsibleSection } from '../base/CollapsibleSection.js';
import { div } from '../../utils/dom.js';
import type { CharacterInstance, SpellSlot } from '../../types/generated/GameState.js';
import type { GameApiService } from '../../services/api/GameApiService.js';

export interface SpellsSectionProps {
  character: CharacterInstance;
  gameId?: string;
  gameApiService?: GameApiService;
  initiallyCollapsed?: boolean;
}

/**
 * Spells section component
 */
export class SpellsSection extends Component<SpellsSectionProps> {
  private collapsibleSection: CollapsibleSection | null = null;
  private spellNameCache: Map<string, string> = new Map();

  constructor(props: SpellsSectionProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const content = div({ class: 'spells-section__content' });

    const spellcasting = this.props.character.state.spellcasting;

    // Check if character has spellcasting
    if (!spellcasting) {
      const noSpells = div(
        { class: 'spells-section__empty' },
        'This character does not have spellcasting abilities.'
      );
      content.appendChild(noSpells);
    } else {

      // Spell slots
      const spellSlots = Object.entries(spellcasting.spell_slots ?? {});
      if (spellSlots.length > 0) {
        const slotsHeader = div({ class: 'spells-section__subheader' }, 'Spell Slots');
        content.appendChild(slotsHeader);

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

        content.appendChild(slotsGrid);
      }

      // Known spells
      const knownSpells = spellcasting.spells_known ?? [];
      if (knownSpells.length > 0) {
        const spellsHeader = div({ class: 'spells-section__subheader' }, 'Known Spells');
        content.appendChild(spellsHeader);

        const spellsList = div({ class: 'known-spells-list' });
        spellsList.id = 'known-spells-list'; // ID for easy reference when updating

        // Initially show spell indexes (will be replaced with names if API call succeeds)
        for (const spell of knownSpells) {
          const displayName = this.spellNameCache.get(spell) ?? spell;
          const spellItem = div({ class: 'spell-item' }, displayName);
          spellsList.appendChild(spellItem);
        }
        content.appendChild(spellsList);
      }
    }

    // Wrap in collapsible section
    this.collapsibleSection = new CollapsibleSection({
      title: 'Spellcasting',
      initiallyCollapsed: this.props.initiallyCollapsed ?? false,
      children: [content],
    });

    const container = div({ class: 'spells-section' });
    this.collapsibleSection.mount(container);

    return container;
  }

  override async onMount(): Promise<void> {
    // Fetch spell names if we have the required props
    const knownSpells = this.props.character.state.spellcasting?.spells_known;
    if (knownSpells && knownSpells.length > 0 && this.props.gameId && this.props.gameApiService) {
      try {
        const response = await this.props.gameApiService.resolveNames(this.props.gameId, {
          spells: knownSpells,
        });

        // Cache the resolved names
        for (const [index, name] of Object.entries(response.spells ?? {})) {
          this.spellNameCache.set(index, name);
        }

        // Update the display with resolved names
        this.updateSpellList();
      } catch (error) {
        console.warn('[SpellsSection] Failed to fetch spell names, showing indexes:', error);
        // Fail gracefully - continue showing indexes
      }
    }
  }

  override onUnmount(): void {
    if (this.collapsibleSection) {
      this.collapsibleSection.unmount();
      this.collapsibleSection = null;
    }
  }

  /**
   * Updates the spell list display with cached names
   */
  private updateSpellList(): void {
    const knownSpells = this.props.character.state.spellcasting?.spells_known;
    if (!knownSpells || knownSpells.length === 0) {
      return;
    }

    const spellsList = this.element?.querySelector('#known-spells-list');
    if (!spellsList) {
      console.warn('[SpellsSection] Could not find spell list element to update');
      return;
    }

    // Clear and rebuild the list with resolved names
    spellsList.innerHTML = '';
    for (const spell of knownSpells) {
      const displayName = this.spellNameCache.get(spell) ?? spell;
      const spellItem = div({ class: 'spell-item' }, displayName);
      spellsList.appendChild(spellItem);
    }
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
