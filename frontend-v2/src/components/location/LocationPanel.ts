/**
 * LocationPanel component
 *
 * Displays current location information including name, description,
 * available exits, and NPCs present.
 */

import { Component } from '../base/Component.js';
import { createElement, div, clearElement } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';

export interface LocationPanelProps {
  stateStore: StateStore;
}

export class LocationPanel extends Component<LocationPanelProps> {
  private descriptionEl: HTMLElement | null = null;
  private exitsEl: HTMLElement | null = null;
  private npcsEl: HTMLElement | null = null;

  protected render(): HTMLElement {
    const container = div({ class: 'location-panel' });

    // Header
    const header = div({ class: 'location-panel__header' });
    const title = createElement('h2', { class: 'location-panel__title' });
    title.textContent = 'Location';
    header.appendChild(title);

    // Location name
    const locationName = createElement('h3', { class: 'location-panel__location-name' });
    locationName.textContent = '—';
    locationName.id = 'location-name';

    // Description
    const descriptionSection = div({ class: 'location-panel__section' });
    const descLabel = createElement('h4', { class: 'location-panel__label' });
    descLabel.textContent = 'Description';
    this.descriptionEl = div({ class: 'location-panel__description' });
    descriptionSection.appendChild(descLabel);
    descriptionSection.appendChild(this.descriptionEl);

    // Exits
    const exitsSection = div({ class: 'location-panel__section' });
    const exitsLabel = createElement('h4', { class: 'location-panel__label' });
    exitsLabel.textContent = 'Exits';
    this.exitsEl = div({ class: 'location-panel__exits' });
    exitsSection.appendChild(exitsLabel);
    exitsSection.appendChild(this.exitsEl);

    // NPCs Present
    const npcsSection = div({ class: 'location-panel__section' });
    const npcsLabel = createElement('h4', { class: 'location-panel__label' });
    npcsLabel.textContent = 'NPCs Present';
    this.npcsEl = div({ class: 'location-panel__npcs' });
    npcsSection.appendChild(npcsLabel);
    npcsSection.appendChild(this.npcsEl);

    container.appendChild(header);
    container.appendChild(locationName);
    container.appendChild(descriptionSection);
    container.appendChild(exitsSection);
    container.appendChild(npcsSection);

    return container;
  }

  override onMount(): void {
    // Subscribe to game state changes
    this.subscribeImmediate(
      this.props.stateStore.gameState$,
      (gameState) => {
        if (gameState) {
          this.updateLocation(gameState);
        } else {
          this.clearLocation();
        }
      }
    );
  }

  private updateLocation(gameState: any): void {
    if (!this.element) return;

    // Get current location ID from scenario instance
    const currentLocationId = gameState.scenario_instance?.current_location_id;

    if (!currentLocationId) {
      this.clearLocation();
      return;
    }

    // Find location definition in scenario sheet
    const locationDef = gameState.scenario_instance?.sheet?.locations?.find(
      (loc: any) => loc.id === currentLocationId
    );

    // Update location name
    const nameEl = this.element.querySelector('#location-name');
    if (nameEl) {
      nameEl.textContent = locationDef?.name || currentLocationId;
    }

    // Update description
    if (this.descriptionEl) {
      clearElement(this.descriptionEl);

      if (locationDef?.description) {
        this.descriptionEl.textContent = locationDef.description;
      } else {
        const placeholder = div({ class: 'location-panel__empty' });
        placeholder.textContent = 'No description available';
        this.descriptionEl.appendChild(placeholder);
      }
    }

    // Update exits/connections
    if (this.exitsEl) {
      clearElement(this.exitsEl);

      const connections = locationDef?.connections;
      if (connections && connections.length > 0) {
        connections.forEach((conn: any) => {
          const connItem = div({
            class: `location-panel__exit-item ${conn.is_accessible === false ? 'blocked' : ''}`
          });

          let content = '';
          if (conn.direction) {
            content += `<span class="exit-direction">[${conn.direction.toUpperCase()}]</span> `;
          }
          content += `<span class="exit-description">${conn.description}</span>`;
          if (conn.is_accessible === false) {
            content += ' <span class="exit-blocked">(Blocked)</span>';
          }

          connItem.innerHTML = content;
          this.exitsEl!.appendChild(connItem);
        });
      } else {
        const noExits = div({ class: 'location-panel__empty' });
        noExits.textContent = 'No visible exits';
        this.exitsEl.appendChild(noExits);
      }
    }

    // Update NPCs present at this location
    if (this.npcsEl) {
      clearElement(this.npcsEl);

      const npcsAtLocation = (gameState.npcs || []).filter(
        (npc: any) => npc.current_location_id === currentLocationId
      );

      if (npcsAtLocation.length > 0) {
        npcsAtLocation.forEach((npc: any) => {
          const npcTag = div({ class: 'location-panel__npc-tag' });
          const displayName = npc.sheet?.display_name ||
                            npc.sheet?.character?.name ||
                            'Unknown NPC';
          npcTag.textContent = displayName;
          this.npcsEl!.appendChild(npcTag);
        });
      } else {
        const noNpcs = div({ class: 'location-panel__empty' });
        noNpcs.textContent = 'No NPCs present';
        this.npcsEl.appendChild(noNpcs);
      }
    }
  }

  private clearLocation(): void {
    const nameEl = this.element?.querySelector('#location-name');
    if (nameEl) {
      nameEl.textContent = '—';
    }

    if (this.descriptionEl) {
      this.descriptionEl.textContent = '';
    }

    if (this.exitsEl) {
      clearElement(this.exitsEl);
    }

    if (this.npcsEl) {
      clearElement(this.npcsEl);
    }
  }
}
