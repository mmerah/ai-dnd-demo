/**
 * CharacterSheetPanel Component
 *
 * Main panel for character sheet display with all sections.
 * Displays the selected party member (player character or NPC).
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { AbilitiesSection } from './AbilitiesSection.js';
import { SkillsSection } from './SkillsSection.js';
import { FeaturesSection } from './FeaturesSection.js';
import { SpellsSection } from './SpellsSection.js';
import type { CharacterInstance, NPCInstance, GameState } from '../../types/generated/GameState.js';

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
      this.props.stateStore.gameState$,
      () => {
        this.handleStateChange();
      }
    );

    // Subscribe to selected member changes
    this.subscribe(
      this.props.stateStore.selectedMemberId$,
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

  /**
   * Get the currently selected member (player character or NPC)
   */
  private getSelectedMember(gameState: GameState): CharacterInstance | NPCInstance | null {
    const selectedId = this.props.stateStore.getSelectedMemberId();

    // Check if it's the player character
    if (gameState.character.instance_id === selectedId) {
      return gameState.character;
    }

    // Check if it's an NPC party member
    const npcs = gameState.npcs ?? [];
    const npc = npcs.find(n => n.instance_id === selectedId);
    if (npc) {
      return npc;
    }

    // Default to player character if nothing selected or invalid ID
    return gameState.character;
  }

  /**
   * Check if a member is an NPC
   */
  private isNPC(member: CharacterInstance | NPCInstance): member is NPCInstance {
    return 'scenario_npc_id' in member;
  }

  private renderHeader(): HTMLElement {
    const gameState = this.props.stateStore.getGameState();
    const header = div({ class: 'character-sheet-panel__header' });

    if (gameState) {
      const member = this.getSelectedMember(gameState);
      if (member) {
        // Character info
        const info = div({ class: 'character-sheet-panel__info' });

        let name: string;
        let race: string;
        let className: string;

        if (this.isNPC(member)) {
          // NPC
          name = member.sheet.display_name;
          race = member.sheet.character?.race ?? 'NPC';
          className = member.sheet.character?.class_index ?? member.sheet.role;
        } else {
          // Player Character
          name = member.sheet.name;
          race = member.sheet.race;
          className = member.sheet.class_index;
        }

        const nameEl = div({ class: 'character-sheet-panel__name' }, name);
        const details = div(
          { class: 'character-sheet-panel__details' },
          `${race} ${className} • Level ${member.state.level ?? 1}`
        );
        const hp = div(
          { class: 'character-sheet-panel__hp' },
          `HP: ${member.state.hit_points.current}/${member.state.hit_points.maximum} • AC: ${member.state.armor_class ?? 10}`
        );

        info.appendChild(nameEl);
        info.appendChild(details);
        info.appendChild(hp);

        header.appendChild(info);
      }
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

    const member = this.getSelectedMember(gameState);
    if (!member) {
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

    // Render all sections with the selected member
    // Cast to CharacterInstance since sections expect this type
    // (NPCs have the same structure via their embedded character sheet)
    this.abilitiesSection = new AbilitiesSection({ character: member as CharacterInstance });
    this.abilitiesSection.mount(content);

    this.skillsSection = new SkillsSection({ character: member as CharacterInstance });
    this.skillsSection.mount(content);

    this.featuresSection = new FeaturesSection({ character: member as CharacterInstance });
    this.featuresSection.mount(content);

    this.spellsSection = new SpellsSection({ character: member as CharacterInstance });
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
