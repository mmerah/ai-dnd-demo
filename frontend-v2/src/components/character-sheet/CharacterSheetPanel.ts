/**
 * CharacterSheetPanel Component
 *
 * Main panel for character sheet display with all sections.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { AbilitiesSection } from './AbilitiesSection.js';
import { SkillsSection } from './SkillsSection.js';
import { FeaturesSection } from './FeaturesSection.js';
import { SpellsSection } from './SpellsSection.js';

export interface CharacterSheetPanelProps {
  stateStore: StateStore;
}

/**
 * Character sheet panel component
 */
export class CharacterSheetPanel extends Component<CharacterSheetPanelProps> {
  private abilitiesSection: AbilitiesSection | null = null;
  private skillsSection: SkillsSection | null = null;
  private featuresSection: FeaturesSection | null = null;
  private spellsSection: SpellsSection | null = null;

  constructor(props: CharacterSheetPanelProps) {
    super(props);
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribe(
      this.props.stateStore['gameState'],
      () => {
        this.handleStateChange();
      }
    );

    // Initial render
    this.handleStateChange();
  }

  protected render(): HTMLElement {
    const container = div({ class: 'character-sheet-panel' });

    // Header with character info and back button
    const header = this.renderHeader();
    container.appendChild(header);

    // Scrollable content area
    const content = div({ class: 'character-sheet-panel__content' });
    container.appendChild(content);

    return container;
  }

  private renderHeader(): HTMLElement {
    const gameState = this.props.stateStore.getGameState();
    const header = div({ class: 'character-sheet-panel__header' });

    if (gameState) {
      const { player } = gameState;

      // Character info
      const info = div({ class: 'character-sheet-panel__info' });
      const name = div({ class: 'character-sheet-panel__name' }, player.name);
      const details = div(
        { class: 'character-sheet-panel__details' },
        `${player.race} ${player.class} • Level ${player.level}`
      );
      const hp = div(
        { class: 'character-sheet-panel__hp' },
        `HP: ${player.hp}/${player.max_hp} • AC: ${player.ac}`
      );

      info.appendChild(name);
      info.appendChild(details);
      info.appendChild(hp);

      header.appendChild(info);
    }

    // Back button
    const backBtn = button('← Back to Party', {
      class: 'character-sheet-panel__back-button',
      onclick: () => this.handleBack(),
    });
    header.appendChild(backBtn);

    return header;
  }

  private handleStateChange(): void {
    const gameState = this.props.stateStore.getGameState();
    if (!gameState || !this.element) {
      return;
    }

    // Update header
    const existingHeader = this.element.querySelector('.character-sheet-panel__header');
    if (existingHeader) {
      const newHeader = this.renderHeader();
      existingHeader.replaceWith(newHeader);
    }

    // Get or create content container
    let content = this.element.querySelector('.character-sheet-panel__content') as HTMLElement;
    if (!content) {
      content = div({ class: 'character-sheet-panel__content' });
      this.element.appendChild(content);
    }

    // Clear and re-render sections
    this.unmountSections();
    content.innerHTML = '';

    // Render all sections
    this.abilitiesSection = new AbilitiesSection({ character: gameState.player });
    this.abilitiesSection.mount(content);

    this.skillsSection = new SkillsSection({ character: gameState.player });
    this.skillsSection.mount(content);

    this.featuresSection = new FeaturesSection({ character: gameState.player });
    this.featuresSection.mount(content);

    this.spellsSection = new SpellsSection({ character: gameState.player });
    this.spellsSection.mount(content);
  }

  private handleBack(): void {
    this.props.stateStore.setRightPanelView('party');
  }

  private unmountSections(): void {
    if (this.abilitiesSection) {
      this.abilitiesSection.unmount();
      this.abilitiesSection = null;
    }
    if (this.skillsSection) {
      this.skillsSection.unmount();
      this.skillsSection = null;
    }
    if (this.featuresSection) {
      this.featuresSection.unmount();
      this.featuresSection = null;
    }
    if (this.spellsSection) {
      this.spellsSection.unmount();
      this.spellsSection = null;
    }
  }

  override onUnmount(): void {
    this.unmountSections();
  }
}
