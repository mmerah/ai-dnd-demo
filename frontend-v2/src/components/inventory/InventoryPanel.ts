/**
 * InventoryPanel Component
 *
 * Main panel for inventory display with currency, equipment, and items.
 * Displays the selected party member's inventory (player character or NPC).
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { CurrencyDisplay } from './CurrencyDisplay.js';
import { EquipmentSlots } from './EquipmentSlots.js';
import { ItemList } from './ItemList.js';
import type { CharacterInstance, NPCInstance, GameState } from '../../types/generated/GameState.js';

export interface InventoryPanelProps {
  stateStore: StateStore;
}

/**
 * Inventory panel component
 */
export class InventoryPanel extends Component<InventoryPanelProps> {
  private currencyDisplay: CurrencyDisplay | null = null;
  private equipmentSlots: EquipmentSlots | null = null;
  private itemList: ItemList | null = null;

  constructor(props: InventoryPanelProps) {
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
    const container = div({ class: 'inventory-panel' });

    // Header with back button
    const header = this.renderHeader();
    container.appendChild(header);

    // Scrollable content area
    const content = div({ class: 'inventory-panel__content' });
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

  private renderHeader(): HTMLElement {
    const header = div({ class: 'inventory-panel__header' });

    const title = div({ class: 'inventory-panel__title' }, 'Inventory');
    header.appendChild(title);

    // Back button
    const backBtn = button('← Back to Party', {
      class: 'inventory-panel__back-button',
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

    // Get or create content container
    let content = this.element.querySelector('.inventory-panel__content') as HTMLElement;
    if (!content) {
      content = div({ class: 'inventory-panel__content' });
      this.element.appendChild(content);
    }

    // Clear and re-render sections
    this.unmountSections();
    content.innerHTML = '';

    // Currency section - pass actual currency data from selected member's state
    const currency = member.state.currency;
    this.currencyDisplay = new CurrencyDisplay({
      copper: currency?.copper,
      silver: currency?.silver,
      electrum: currency?.electrum,
      gold: currency?.gold,
      platinum: currency?.platinum,
    });
    this.currencyDisplay.mount(content);

    // Equipment section
    const equipment = member.state.equipment_slots;
    this.equipmentSlots = new EquipmentSlots({ equipment: equipment ?? {} });
    this.equipmentSlots.mount(content);

    // Items section
    const inventory = member.state.inventory ?? [];
    this.itemList = new ItemList({ items: inventory });
    this.itemList.mount(content);
  }

  private handleBack(): void {
    this.props.stateStore.setRightPanelView('party');
  }

  private unmountSections(): void {
    if (this.currencyDisplay) {
      this.currencyDisplay.unmount();
      this.currencyDisplay = null;
    }
    if (this.equipmentSlots) {
      this.equipmentSlots.unmount();
      this.equipmentSlots = null;
    }
    if (this.itemList) {
      this.itemList.unmount();
      this.itemList = null;
    }
  }

  override onUnmount(): void {
    this.unmountSections();
  }
}
