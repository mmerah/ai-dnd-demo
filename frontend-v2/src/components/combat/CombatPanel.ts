/**
 * CombatPanel component
 *
 * Displays combat status including round number, current turn, and turn order.
 * Automatically shows/hides based on combat state.
 */

import { Component } from '../base/Component.js';
import { createElement, clearElement } from '../../utils/dom.js';
import type { StateStore } from '../../services/state/StateStore.js';
import type {
  GameState,
  CombatState,
  CombatParticipant,
} from '../../types/generated/GameState.js';

export interface CombatPanelProps {
  stateStore: StateStore;
}

interface ParticipantDisplay {
  participant: CombatParticipant;
  isCurrent: boolean;
  hpCurrent?: number;
  hpMaximum?: number;
}

export class CombatPanel extends Component<CombatPanelProps> {
  private container: HTMLElement | null = null;
  private roundElement: HTMLElement | null = null;
  private currentTurnElement: HTMLElement | null = null;
  private turnOrderList: HTMLElement | null = null;

  protected render(): HTMLElement {
    this.container = createElement('div', {
      class: 'combat-panel',
      style: 'display: none;', // Hidden by default
    });

    // Header
    const header = createElement('div', {
      class: 'combat-panel__header',
    });

    const title = createElement('h3', {
      class: 'combat-panel__title',
    });
    title.textContent = '⚔️ Combat Status';
    header.appendChild(title);

    // Combat info container
    const infoContainer = createElement('div', {
      class: 'combat-panel__info',
    });

    // Combat header (round and current turn)
    const combatHeader = createElement('div', {
      class: 'combat-panel__combat-header',
    });

    // Round display
    const roundDiv = createElement('div', {
      class: 'combat-panel__round',
    });
    const roundLabel = createElement('span', {
      class: 'combat-panel__label',
    });
    roundLabel.textContent = 'Round:';
    this.roundElement = createElement('span', {
      class: 'combat-panel__value',
    });
    this.roundElement.textContent = '1';
    roundDiv.appendChild(roundLabel);
    roundDiv.appendChild(this.roundElement);

    // Current turn display
    const turnDiv = createElement('div', {
      class: 'combat-panel__turn',
    });
    const turnLabel = createElement('span', {
      class: 'combat-panel__label',
    });
    turnLabel.textContent = 'Current Turn:';
    this.currentTurnElement = createElement('span', {
      class: 'combat-panel__value',
    });
    this.currentTurnElement.textContent = '-';
    turnDiv.appendChild(turnLabel);
    turnDiv.appendChild(this.currentTurnElement);

    combatHeader.appendChild(roundDiv);
    combatHeader.appendChild(turnDiv);

    // Turn order section
    const turnOrderSection = createElement('div', {
      class: 'combat-panel__turn-order',
    });
    const turnOrderTitle = createElement('h4', {
      class: 'combat-panel__turn-order-title',
    });
    turnOrderTitle.textContent = 'Turn Order:';

    this.turnOrderList = createElement('div', {
      class: 'combat-panel__turn-order-list',
    });

    turnOrderSection.appendChild(turnOrderTitle);
    turnOrderSection.appendChild(this.turnOrderList);

    // Assemble
    infoContainer.appendChild(combatHeader);
    infoContainer.appendChild(turnOrderSection);

    this.container.appendChild(header);
    this.container.appendChild(infoContainer);

    return this.container;
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribeImmediate(
      this.props.stateStore.gameState$,
      (gameState) => {
        this.updateCombatDisplay(gameState);
      }
    );
  }

  private updateCombatDisplay(gameState: GameState | null): void {
    if (!this.container || !gameState) {
      this.hideCombatPanel();
      return;
    }

    const combat = gameState.combat;

    // Show/hide based on combat state
    if (!combat || !combat.is_active) {
      this.hideCombatPanel();
      return;
    }

    this.showCombatPanel();
    this.updateCombatInfo(combat, gameState);
  }

  private showCombatPanel(): void {
    if (this.container) {
      this.container.style.display = 'block';
    }
  }

  private hideCombatPanel(): void {
    if (this.container) {
      this.container.style.display = 'none';
    }
  }

  private updateCombatInfo(combat: CombatState, gameState: GameState): void {
    // Update round number
    if (this.roundElement) {
      this.roundElement.textContent = String(combat.round_number ?? 1);
    }

    // Check if we have participants
    if (!combat.participants || combat.participants.length === 0) {
      if (this.currentTurnElement) {
        this.currentTurnElement.textContent = 'No participants';
      }
      if (this.turnOrderList) {
        clearElement(this.turnOrderList);
        const noParticipants = createElement('div', {
          class: 'combat-panel__no-participants',
        });
        noParticipants.textContent = 'No participants in combat';
        this.turnOrderList.appendChild(noParticipants);
      }
      return;
    }

    // Find current turn participant
    const activeParticipants = combat.participants.filter(
      (p) => p.is_active !== false
    );
    const currentIndex = Math.min(
      combat.turn_index ?? 0,
      activeParticipants.length - 1
    );
    const currentParticipant = activeParticipants[currentIndex];

    // Update current turn name
    if (this.currentTurnElement && currentParticipant) {
      this.currentTurnElement.textContent = currentParticipant.name;
    }

    // Build turn order list
    this.renderTurnOrder(combat, gameState, currentParticipant);
  }

  private renderTurnOrder(
    combat: CombatState,
    gameState: GameState,
    currentParticipant?: CombatParticipant
  ): void {
    if (!this.turnOrderList || !combat.participants) return;

    clearElement(this.turnOrderList);

    // Sort by initiative (highest first)
    const sortedParticipants = [...combat.participants].sort((a, b) => {
      const initA = a.initiative ?? -1;
      const initB = b.initiative ?? -1;
      return initB - initA;
    });

    // Build participant displays with HP info
    const participantDisplays: ParticipantDisplay[] = sortedParticipants
      .filter((p) => p.is_active !== false)
      .map((participant) => {
        const isCurrent =
          currentParticipant?.entity_id === participant.entity_id;

        // Get HP info based on entity type
        let hpCurrent: number | undefined;
        let hpMaximum: number | undefined;

        if (participant.entity_type === 'player' && gameState.character) {
          const hp = gameState.character.state.hit_points;
          if (hp) {
            hpCurrent = hp.current;
            hpMaximum = hp.maximum;
          }
        } else if (participant.entity_type === 'monster' && gameState.monsters) {
          const monster = gameState.monsters.find(
            (m) => m.instance_id === participant.entity_id
          );
          if (monster?.state?.hit_points) {
            hpCurrent = monster.state.hit_points.current;
            hpMaximum = monster.state.hit_points.maximum;
          }
        } else if (participant.entity_type === 'npc' && gameState.npcs) {
          const npc = gameState.npcs.find(
            (n) => n.instance_id === participant.entity_id
          );
          if (npc?.state?.hit_points) {
            hpCurrent = npc.state.hit_points.current;
            hpMaximum = npc.state.hit_points.maximum;
          }
        }

        return {
          participant,
          isCurrent,
          hpCurrent,
          hpMaximum,
        };
      });

    // Render each participant
    participantDisplays.forEach((display) => {
      const participantEl = this.createParticipantElement(display);
      this.turnOrderList!.appendChild(participantEl);
    });
  }

  private createParticipantElement(display: ParticipantDisplay): HTMLElement {
    const { participant, isCurrent, hpCurrent, hpMaximum } = display;

    const participantDiv = createElement('div', {
      class: 'combat-panel__participant',
    });

    if (isCurrent) {
      participantDiv.classList.add('combat-panel__participant--current');
    }

    // Turn arrow
    const arrow = createElement('span', {
      class: 'combat-panel__turn-arrow',
    });
    arrow.textContent = isCurrent ? '→' : '';

    // Initiative
    const initiativeEl = createElement('span', {
      class: 'combat-panel__initiative',
    });
    initiativeEl.textContent = String(participant.initiative ?? '?');

    // Name and tags
    const nameEl = createElement('span', {
      class: 'combat-panel__participant-name',
    });

    let nameText = participant.name;
    if (participant.is_player) {
      nameText += ' [PLAYER]';
    }
    nameEl.textContent = nameText;

    // HP display
    const hpEl = createElement('span', {
      class: 'combat-panel__participant-hp',
    });

    if (hpCurrent !== undefined && hpMaximum !== undefined) {
      hpEl.textContent = `(${hpCurrent}/${hpMaximum} HP)`;
    }

    participantDiv.appendChild(arrow);
    participantDiv.appendChild(initiativeEl);
    participantDiv.appendChild(nameEl);
    if (hpEl.textContent) {
      participantDiv.appendChild(hpEl);
    }

    return participantDiv;
  }
}
