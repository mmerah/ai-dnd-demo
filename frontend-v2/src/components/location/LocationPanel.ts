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
          // Location is just a string (ID) in the backend, description is separate
          const locationId = gameState.location?? 'Unknown';
          const description = gameState.description ?? '';
          this.updateLocation(locationId, description);
        } else {
          this.clearLocation();
        }
      }
    );
  }

  private updateLocation(locationId: string, description: string): void {
    if (!this.element) return;

    // Update location name
    const nameEl = this.element.querySelector('#location-name');
    if (nameEl) {
      nameEl.textContent = locationId;
    }

    // Update description
    if (this.descriptionEl) {
      this.descriptionEl.textContent = description;
    }

    // Update exits - placeholder for now as we don't have exit data in gameState
    if (this.exitsEl) {
      clearElement(this.exitsEl);
      const noExits = div({ class: 'location-panel__empty' });
      noExits.textContent = 'Exit information not available';
      this.exitsEl.appendChild(noExits);
    }

    // Update NPCs - placeholder for now
    if (this.npcsEl) {
      clearElement(this.npcsEl);
      const noNpcs = div({ class: 'location-panel__empty' });
      noNpcs.textContent = 'NPC information not available';
      this.npcsEl.appendChild(noNpcs);
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
