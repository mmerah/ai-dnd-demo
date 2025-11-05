/**
 * CatalogItemDetail Component
 *
 * Displays detailed information about a selected catalog item.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { Spell, Item, Monster, Race, Class, Background, Feat } from '../../services/api/CatalogApiService.js';

export type CatalogItem = Spell | Item | Monster | Race | Class | Background | Feat;

export interface CatalogItemDetailProps {
  item: CatalogItem | null;
  onClose: () => void;
}

/**
 * Catalog item detail component
 */
export class CatalogItemDetail extends Component<CatalogItemDetailProps> {
  constructor(props: CatalogItemDetailProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const container = div({ class: 'catalog-item-detail' });

    if (!this.props.item) {
      const placeholder = div(
        { class: 'catalog-item-detail__placeholder' },
        'Select an item to view details'
      );
      container.appendChild(placeholder);
      return container;
    }

    // Header with close button
    const header = div({ class: 'catalog-item-detail__header' });
    const title = div({ class: 'catalog-item-detail__title' }, this.props.item.name);
    const closeBtn = button('×', {
      class: 'catalog-item-detail__close',
      onclick: () => this.props.onClose(),
    });
    header.appendChild(title);
    header.appendChild(closeBtn);
    container.appendChild(header);

    // Content
    const content = div({ class: 'catalog-item-detail__content' });
    content.appendChild(this.renderItemDetails(this.props.item));
    container.appendChild(content);

    return container;
  }

  private renderItemDetails(item: CatalogItem): HTMLElement {
    const details = div({ class: 'catalog-item-detail__body' });

    // Render different fields based on item type
    if ('level' in item && 'school' in item) {
      // Spell
      this.renderField(details, 'Level', item.level.toString());
      this.renderField(details, 'School', item.school);
      this.renderField(details, 'Casting Time', item.casting_time);
      this.renderField(details, 'Range', item.range);
      this.renderField(details, 'Components', item.components);
      this.renderField(details, 'Duration', item.duration);
    } else if ('challenge_rating' in item) {
      // Monster
      this.renderField(details, 'Type', item.type);
      this.renderField(details, 'Size', item.size);
      this.renderField(details, 'Challenge Rating', item.challenge_rating);
      this.renderField(details, 'Armor Class', item.armor_class.toString());
      this.renderField(details, 'Hit Points', item.hit_points.toString());
    } else if ('speed' in item && 'size' in item) {
      // Race
      this.renderField(details, 'Size', item.size);
      this.renderField(details, 'Speed', `${item.speed} ft.`);
    } else if ('hit_die' in item) {
      // Class
      this.renderField(details, 'Hit Die', `d${item.hit_die}`);
      this.renderField(details, 'Primary Ability', item.primary_ability);
    } else if ('skill_proficiencies' in item) {
      // Background
      this.renderField(details, 'Skill Proficiencies', item.skill_proficiencies.join(', '));
    } else if ('type' in item) {
      // Item
      this.renderField(details, 'Type', item.type);
      if (item.rarity) {
        this.renderField(details, 'Rarity', item.rarity);
      }
      if (item.cost) {
        this.renderField(details, 'Cost', item.cost);
      }
      if (item.weight) {
        this.renderField(details, 'Weight', `${item.weight} lbs`);
      }
    }

    // Description (common to all)
    const description = div({ class: 'catalog-item-detail__description' });
    const descHeader = div({ class: 'catalog-item-detail__field-label' }, 'Description');
    const descText = div({ class: 'catalog-item-detail__field-value' }, item.description);
    description.appendChild(descHeader);
    description.appendChild(descText);
    details.appendChild(description);

    // Content pack (if present)
    if (item.content_pack) {
      this.renderField(details, 'Content Pack', item.content_pack);
    }

    return details;
  }

  private renderField(container: HTMLElement, label: string, value: string): void {
    const field = div({ class: 'catalog-item-detail__field' });
    const fieldLabel = div({ class: 'catalog-item-detail__field-label' }, label);
    const fieldValue = div({ class: 'catalog-item-detail__field-value' }, value);
    field.appendChild(fieldLabel);
    field.appendChild(fieldValue);
    container.appendChild(field);
  }
}
