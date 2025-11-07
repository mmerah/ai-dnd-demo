/**
 * PartyPanel component
 *
 * Displays all party members with their current status.
 * Allows selecting a member to view their full details.
 */

import { Component } from '../base/Component.js';
import { createElement, div, clearElement, button } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { PartyMemberCard } from './PartyMemberCard.js';
import type { NPCInstance } from '../../types/generated/GameState.js';

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

export interface PartyPanelProps {
  stateStore: StateStore;
}

export class PartyPanel extends Component<PartyPanelProps> {
  private membersContainer: HTMLElement | null = null;
  private memberCards: Map<string, PartyMemberCard> = new Map();
  private partyCountSpan: HTMLElement | null = null;

  protected render(): HTMLElement {
    const container = div({ class: 'party-panel' });

    // Header with party count
    const header = div({ class: 'party-panel__header' });

    const titleRow = div({ class: 'party-panel__title-row' });
    const title = createElement('h2', { class: 'party-panel__title' });
    title.textContent = 'Party';

    this.partyCountSpan = createElement('span', { class: 'party-panel__count' });
    this.partyCountSpan.textContent = '1/4'; // Default, will be updated on mount

    titleRow.appendChild(title);
    titleRow.appendChild(this.partyCountSpan);
    header.appendChild(titleRow);

    // Navigation buttons
    const navButtons = div({ class: 'party-panel__nav-buttons' });

    const characterSheetBtn = button('📋 Character', {
      class: 'party-panel__nav-button',
      onclick: () => this.handleViewCharacterSheet(),
    });

    const inventoryBtn = button('🎒 Inventory', {
      class: 'party-panel__nav-button',
      onclick: () => this.handleViewInventory(),
    });

    navButtons.appendChild(characterSheetBtn);
    navButtons.appendChild(inventoryBtn);
    header.appendChild(navButtons);

    // Members container
    this.membersContainer = div({ class: 'party-panel__members' });

    container.appendChild(header);
    container.appendChild(this.membersContainer);

    return container;
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribeImmediate(
      this.props.stateStore.gameState$,
      (gameState) => {
        if (gameState) {
          const members = this.buildPartyMembers(gameState);
          this.renderMembers(members);
        } else {
          this.clearMembers();
        }
      }
    );

    // Subscribe to selected member changes
    this.subscribe(
      this.props.stateStore.selectedMemberId$,
      () => {
        // Re-render to update selection
        const gameState = this.props.stateStore.getGameState();
        if (gameState) {
          const members = this.buildPartyMembers(gameState);
          this.renderMembers(members);
        }
      }
    );
  }

  private buildPartyMembers(gameState: any): PartyMember[] {
    const character = gameState.character;
    const members: PartyMember[] = [
      {
        id: character.instance_id,
        name: character.sheet.name,
        role: 'Player',
        hp: character.state.hit_points.current,
        max_hp: character.state.hit_points.maximum,
        ac: character.state.armor_class,
        level: character.state.level,
        class_name: character.sheet.class_index,
        conditions: character.state.conditions ?? [],
      },
    ];

    // Add party members from NPCs
    const party = gameState.party;
    const npcs = gameState.npcs ?? [];
    const memberIds = party?.member_ids ?? [];

    for (const npcId of memberIds) {
      const npc = npcs.find((n: NPCInstance) => n.instance_id === npcId);
      if (npc) {
        members.push({
          id: npc.instance_id,
          name: npc.sheet.display_name,
          role: npc.sheet.role,
          hp: npc.state.hit_points.current,
          max_hp: npc.state.hit_points.maximum,
          ac: npc.state.armor_class,
          level: npc.state.level,
          class_name: npc.sheet.character?.class_index ?? 'NPC',
          conditions: npc.state.conditions ?? [],
        });
      }
    }

    return members;
  }

  override onUnmount(): void {
    this.clearMembers();
  }

  private renderMembers(members: PartyMember[]): void {
    if (!this.membersContainer) return;

    // Update party count (shows current/max party size)
    const gameState = this.props.stateStore.getGameState();
    if (this.partyCountSpan && gameState) {
      const maxSize = gameState.party?.max_size ?? 4;
      const currentSize = members.length;
      this.partyCountSpan.textContent = `${currentSize}/${maxSize}`;
    }

    // Clear existing cards
    clearElement(this.membersContainer);
    this.memberCards.forEach(card => card.unmount());
    this.memberCards.clear();

    const selectedId = this.props.stateStore.getSelectedMemberId();

    // Render each member
    members.forEach(member => {
      const card = new PartyMemberCard({
        member,
        isSelected: member.id === selectedId,
        onSelect: (memberId) => this.handleSelectMember(memberId),
      });

      card.mount(this.membersContainer!);
      this.memberCards.set(member.id, card);
    });
  }

  private clearMembers(): void {
    if (!this.membersContainer) return;

    clearElement(this.membersContainer);
    this.memberCards.forEach(card => card.unmount());
    this.memberCards.clear();
  }

  private handleSelectMember(memberId: string): void {
    try {
      this.props.stateStore.setSelectedMemberId(memberId);
    } catch (error) {
      console.error('Failed to select member:', error);
    }
  }

  private handleViewCharacterSheet(): void {
    this.props.stateStore.setRightPanelView('character-sheet');
  }

  private handleViewInventory(): void {
    this.props.stateStore.setRightPanelView('inventory');
  }
}
