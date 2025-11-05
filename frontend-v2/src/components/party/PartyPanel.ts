/**
 * PartyPanel component
 *
 * Displays all party members with their current status.
 * Allows selecting a member to view their full details.
 */

import { Component } from '../base/Component.js';
import { createElement, div, clearElement } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { PartyMemberCard } from './PartyMemberCard.js';
import { PartyMember } from '../../types/generated/GameState.js';

export interface PartyPanelProps {
  stateStore: StateStore;
}

export class PartyPanel extends Component<PartyPanelProps> {
  private membersContainer: HTMLElement | null = null;
  private memberCards: Map<string, PartyMemberCard> = new Map();

  protected render(): HTMLElement {
    const container = div({ class: 'party-panel' });

    // Header
    const header = div({ class: 'party-panel__header' });
    const title = createElement('h2', { class: 'party-panel__title' });
    title.textContent = 'Party';
    header.appendChild(title);

    // Members container
    this.membersContainer = div({ class: 'party-panel__members' });

    container.appendChild(header);
    container.appendChild(this.membersContainer);

    return container;
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribeImmediate(
      this.props.stateStore['gameState'],
      (gameState) => {
        if (gameState) {
          // Include player as first member
          const members: PartyMember[] = [
            {
              id: 'player',
              name: gameState.player.name,
              role: 'player',
              hp: gameState.player.hp,
              max_hp: gameState.player.max_hp,
              ac: gameState.player.ac,
              level: gameState.player.level,
              class_name: gameState.player.class,
            },
            ...gameState.party.members,
          ];
          this.renderMembers(members);
        } else {
          this.clearMembers();
        }
      }
    );

    // Subscribe to selected member changes
    this.subscribe(
      this.props.stateStore['selectedMemberId'],
      () => {
        // Re-render to update selection
        const gameState = this.props.stateStore.getGameState();
        if (gameState) {
          const members: PartyMember[] = [
            {
              id: 'player',
              name: gameState.player.name,
              role: 'player',
              hp: gameState.player.hp,
              max_hp: gameState.player.max_hp,
              ac: gameState.player.ac,
              level: gameState.player.level,
              class_name: gameState.player.class,
            },
            ...gameState.party.members,
          ];
          this.renderMembers(members);
        }
      }
    );
  }

  override onUnmount(): void {
    this.clearMembers();
  }

  private renderMembers(members: PartyMember[]): void {
    if (!this.membersContainer) return;

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
}
