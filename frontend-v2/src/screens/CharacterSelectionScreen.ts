/**
 * CharacterSelectionScreen
 *
 * Screen for selecting a pre-made character to start a new game.
 */

import { Screen } from './Screen.js';
import { ServiceContainer } from '../container.js';
import { div, button } from '../utils/dom.js';
import { CharacterCard, type CharacterCardProps } from '../components/character/CharacterCard.js';
import type { Character } from '../services/api/CatalogApiService.js';

export interface CharacterSelectionScreenProps {
  container: ServiceContainer;
  onBack: () => void;
  onNext: (characterId: string) => void;
}

/**
 * Character selection screen
 */
export class CharacterSelectionScreen extends Screen {
  private charactersContainer: HTMLElement | null = null;
  private loadingIndicator: HTMLElement | null = null;
  private errorDisplay: HTMLElement | null = null;
  private nextButton: HTMLButtonElement | null = null;
  private characterCards: CharacterCard[] = [];
  private selectedCharacterId: string | null = null;
  private characters: Character[] = [];

  constructor(private props: CharacterSelectionScreenProps) {
    super();
  }

  protected render(): HTMLElement {
    const screen = div({ class: 'character-selection-screen' });

    // Header
    const header = div({ class: 'character-selection-screen__header' });
    const title = div({ class: 'character-selection-screen__title' }, 'Select Your Character');
    header.appendChild(title);

    // Content container
    const content = div({ class: 'character-selection-screen__content' });

    // Loading indicator
    this.loadingIndicator = div(
      { class: 'character-selection-screen__loading' },
      'Loading characters...'
    );

    // Error display
    this.errorDisplay = div({ class: 'character-selection-screen__error' });
    this.errorDisplay.style.display = 'none';

    // Characters container
    this.charactersContainer = div({ class: 'character-selection-screen__characters' });

    content.appendChild(this.loadingIndicator);
    content.appendChild(this.errorDisplay);
    content.appendChild(this.charactersContainer);

    // Navigation footer
    const footer = div({ class: 'character-selection-screen__footer' });

    const backButton = button('Back', {
      class: 'character-selection-screen__back-btn',
      onclick: () => this.props.onBack(),
    });

    this.nextButton = button('Next', {
      class: 'character-selection-screen__next-btn',
      disabled: true,
      onclick: () => this.handleNext(),
    }) as HTMLButtonElement;

    footer.appendChild(backButton);
    footer.appendChild(this.nextButton);

    screen.appendChild(header);
    screen.appendChild(content);
    screen.appendChild(footer);

    return screen;
  }

  override onMount(): void {
    this.loadCharacters();
  }

  override onUnmount(): void {
    // Clean up character cards
    this.characterCards.forEach((card) => card.unmount());
    this.characterCards = [];
  }

  private async loadCharacters(): Promise<void> {
    const { container } = this.props;

    try {
      this.showLoading();

      const response = await container.catalogApiService.getCharacters();
      this.characters = response.characters;

      if (this.characters.length === 0) {
        this.showError('No characters available');
      } else {
        this.showCharacters(this.characters);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
      const message = error instanceof Error ? error.message : 'Failed to load characters';
      this.showError(message);
    }
  }

  private showLoading(): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.charactersContainer) return;

    this.loadingIndicator.style.display = 'block';
    this.errorDisplay.style.display = 'none';
    this.charactersContainer.innerHTML = '';
  }

  private showError(message: string): void {
    if (!this.loadingIndicator || !this.errorDisplay) return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'block';
    this.errorDisplay.innerHTML = `
      <div class="character-selection-screen__error-title">Failed to Load Characters</div>
      <div class="character-selection-screen__error-message">${message}</div>
      <button class="character-selection-screen__retry-btn">Retry</button>
    `;

    const retryBtn = this.errorDisplay.querySelector('.character-selection-screen__retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.loadCharacters());
    }
  }

  private showCharacters(characters: Character[]): void {
    if (!this.loadingIndicator || !this.errorDisplay || !this.charactersContainer) return;

    this.loadingIndicator.style.display = 'none';
    this.errorDisplay.style.display = 'none';
    this.charactersContainer.innerHTML = '';

    // Clear existing cards
    this.characterCards.forEach((card) => card.unmount());
    this.characterCards = [];

    // Create and mount character cards
    characters.forEach((character) => {
      if (!this.charactersContainer) return;

      const card = new CharacterCard({
        character,
        isSelected: this.selectedCharacterId === character.id,
        onSelect: (characterId) => this.handleSelectCharacter(characterId),
      });

      card.mount(this.charactersContainer);
      this.characterCards.push(card);
    });
  }

  private handleSelectCharacter(characterId: string): void {
    this.selectedCharacterId = characterId;

    // Update all cards to reflect selection
    this.characterCards.forEach((card) => {
      const cardProps = card as unknown as { props: CharacterCardProps };
      const isSelected = cardProps.props.character.id === characterId;
      card.update({ isSelected });
    });

    // Enable next button
    if (this.nextButton) {
      this.nextButton.disabled = false;
    }
  }

  private handleNext(): void {
    if (this.selectedCharacterId) {
      this.props.onNext(this.selectedCharacterId);
    }
  }
}
