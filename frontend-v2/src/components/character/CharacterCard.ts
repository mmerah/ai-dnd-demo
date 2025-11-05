/**
 * CharacterCard Component
 *
 * Displays a selectable character card with basic information.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';
import type { Character } from '../../services/api/CatalogApiService.js';

export interface CharacterCardProps {
  character: Character;
  isSelected: boolean;
  onSelect: (characterId: string) => void;
}

/**
 * Character card component for character selection
 */
export class CharacterCard extends Component<CharacterCardProps> {
  constructor(props: CharacterCardProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { character, isSelected } = this.props;

    const card = div({
      class: `character-card ${isSelected ? 'character-card--selected' : ''}`,
      onclick: () => this.handleSelect(),
    });

    // Character portrait placeholder
    const portrait = div({ class: 'character-card__portrait' });
    const initials = this.getInitials(character.name);
    portrait.textContent = initials;

    // Character info
    const info = div({ class: 'character-card__info' });

    const name = div({ class: 'character-card__name' }, character.name);

    const raceClass = div(
      { class: 'character-card__race-class' },
      `${character.race} ${character.class}`
    );

    const level = div({ class: 'character-card__level' }, `Level ${character.level}`);

    if (character.background) {
      const background = div(
        { class: 'character-card__background' },
        character.background
      );
      info.appendChild(background);
    }

    info.appendChild(name);
    info.appendChild(raceClass);
    info.appendChild(level);

    // Selection indicator
    if (isSelected) {
      const indicator = div({ class: 'character-card__indicator' }, '✓');
      card.appendChild(indicator);
    }

    card.appendChild(portrait);
    card.appendChild(info);

    return card;
  }

  override onUpdate(prevProps: CharacterCardProps): void {
    // Re-render if selection state changed
    if (prevProps.isSelected !== this.props.isSelected) {
      this.rerender();
    }
  }

  private handleSelect(): void {
    this.props.onSelect(this.props.character.id);
  }

  private getInitials(name: string): string {
    const words = name.trim().split(' ').filter(w => w.length > 0);
    if (words.length === 0) return '?';

    const firstWord = words[0];
    if (!firstWord) return '?';

    if (words.length === 1) {
      return firstWord.charAt(0).toUpperCase();
    }

    const lastWord = words[words.length - 1];
    if (!lastWord) return firstWord.charAt(0).toUpperCase();

    return (firstWord.charAt(0) + lastWord.charAt(0)).toUpperCase();
  }

  private rerender(): void {
    if (!this.element) return;

    const parent = this.element.parentElement;
    if (!parent) return;

    this.unmount();
    this.mount(parent);
  }
}
