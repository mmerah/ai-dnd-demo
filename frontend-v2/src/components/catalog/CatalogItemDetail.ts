/**
 * CatalogItemDetail Component
 *
 * Displays detailed information about a selected catalog item.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { SpellDefinition } from '../../types/generated/SpellDefinition.js';
import type { ItemDefinition } from '../../types/generated/ItemDefinition.js';
import type { MonsterSheet } from '../../types/generated/MonsterSheet.js';
import type { RaceDefinition } from '../../types/generated/RaceDefinition.js';
import type { ClassDefinition } from '../../types/generated/ClassDefinition.js';
import type { BackgroundDefinition } from '../../types/generated/BackgroundDefinition.js';
import type { FeatDefinition } from '../../types/generated/FeatDefinition.js';

export type CatalogItem =
  | SpellDefinition
  | ItemDefinition
  | MonsterSheet
  | RaceDefinition
  | ClassDefinition
  | BackgroundDefinition
  | FeatDefinition;

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
      // SpellDefinition
      this.renderField(details, 'Level', item.level.toString());
      this.renderField(details, 'School', item.school);
      this.renderField(details, 'Casting Time', item.casting_time);
      this.renderField(details, 'Range', item.range);
      if (item.components_list) {
        this.renderField(details, 'Components', item.components_list.join(', '));
      }
      this.renderField(details, 'Duration', item.duration);
    } else if ('challenge_rating' in item) {
      // MonsterSheet
      this.renderField(details, 'Type', item.type);
      this.renderField(details, 'Size', item.size);
      this.renderField(details, 'Challenge Rating', item.challenge_rating.toString());
      this.renderField(details, 'Armor Class', item.armor_class.toString());
      this.renderField(details, 'Hit Points', `${item.hit_points.current}/${item.hit_points.maximum}`);
      this.renderField(details, 'Speed', item.speed);
      this.renderField(details, 'Alignment', item.alignment);
    } else if ('speed' in item && 'size' in item) {
      // RaceDefinition
      this.renderField(details, 'Size', item.size);
      this.renderField(details, 'Speed', `${item.speed} ft.`);
    } else if ('hit_die' in item) {
      // ClassDefinition
      this.renderField(details, 'Hit Die', `d${item.hit_die}`);
      this.renderField(details, 'Saving Throws', item.saving_throws.join(', '));
    } else if ('skill_proficiencies' in item) {
      // BackgroundDefinition
      if (item.skill_proficiencies) {
        this.renderField(details, 'Skill Proficiencies', item.skill_proficiencies.join(', '));
      }
    } else if ('type' in item) {
      // ItemDefinition
      this.renderField(details, 'Type', item.type);
      this.renderField(details, 'Rarity', item.rarity);
      if (item.weight) {
        this.renderField(details, 'Weight', `${item.weight} lbs`);
      }
      if (item.value) {
        this.renderField(details, 'Value', `${item.value} gp`);
      }
    }

    // Description (if available - MonsterSheet doesn't have description field)
    if ('description' in item && item.description) {
      const description = div({ class: 'catalog-item-detail__description' });
      const descHeader = div({ class: 'catalog-item-detail__field-label' }, 'Description');
      const descText = div({ class: 'catalog-item-detail__field-value' }, item.description);
      description.appendChild(descHeader);
      description.appendChild(descText);
      details.appendChild(description);
    }

    // Content pack (common to all)
    this.renderField(details, 'Content Pack', item.content_pack);

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
