/**
 * LocationPanel component
 *
 * Displays current location information including name, description,
 * available exits, and NPCs present.
 */

import { Component } from '../base/Component.js';
import { createElement, div, clearElement } from '../../utils/dom.js';
import { StateStore } from '../../services/state/StateStore.js';
import { Location } from '../../types/generated/GameState.js';

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
      this.props.stateStore['gameState'],
      (gameState) => {
        if (gameState) {
          this.updateLocation(gameState.location);
        } else {
          this.clearLocation();
        }
      }
    );
  }

  private updateLocation(location: Location): void {
    if (!this.element) return;

    // Update location name
    const nameEl = this.element.querySelector('#location-name');
    if (nameEl) {
      nameEl.textContent = location.name;
    }

    // Update description
    if (this.descriptionEl) {
      this.descriptionEl.textContent = location.description;
    }

    // Update exits
    if (this.exitsEl) {
      clearElement(this.exitsEl);

      if (Object.keys(location.exits).length === 0) {
        const noExits = div({ class: 'location-panel__empty' });
        noExits.textContent = 'No visible exits';
        this.exitsEl.appendChild(noExits);
      } else {
        const exitList = createElement('ul', { class: 'location-panel__exit-list' });

        Object.entries(location.exits).forEach(([direction, destination]) => {
          const exitItem = createElement('li', { class: 'location-panel__exit-item' });
          const directionSpan = createElement('span', { class: 'location-panel__exit-direction' });
          directionSpan.textContent = direction;
          const destinationSpan = createElement('span', { class: 'location-panel__exit-destination' });
          destinationSpan.textContent = destination;

          exitItem.appendChild(directionSpan);
          exitItem.appendChild(document.createTextNode(' → '));
          exitItem.appendChild(destinationSpan);

          exitList.appendChild(exitItem);
        });

        this.exitsEl.appendChild(exitList);
      }
    }

    // Update NPCs
    if (this.npcsEl) {
      clearElement(this.npcsEl);

      if (location.npcs_present.length === 0) {
        const noNpcs = div({ class: 'location-panel__empty' });
        noNpcs.textContent = 'No NPCs present';
        this.npcsEl.appendChild(noNpcs);
      } else {
        const npcList = createElement('ul', { class: 'location-panel__npc-list' });

        location.npcs_present.forEach(npcId => {
          const npcItem = createElement('li', { class: 'location-panel__npc-item' });
          npcItem.textContent = npcId; // TODO: Look up NPC name from ID
          npcList.appendChild(npcItem);
        });

        this.npcsEl.appendChild(npcList);
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
