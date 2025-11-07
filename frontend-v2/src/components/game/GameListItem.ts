/**
 * GameListItem Component
 *
 * Displays a single saved game card with load and delete functionality.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';

export interface GameListItemProps {
  gameId: string;
  scenarioName: string;
  characterName: string;
  lastSaved: string;
  createdAt: string;
  onLoad: (gameId: string) => void;
  onDelete: (gameId: string) => void;
}

/**
 * Game list item card component
 */
export class GameListItem extends Component<GameListItemProps> {
  constructor(props: GameListItemProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { scenarioName, characterName, lastSaved, createdAt } = this.props;

    const card = div({ class: 'game-list-item' });

    // Scenario name
    const scenarioTitle = div({ class: 'game-list-item__scenario' }, scenarioName);

    // Character name
    const characterInfo = div({ class: 'game-list-item__character' }, `Character: ${characterName}`);

    // Timestamps section - show relative time for last saved
    const timestampsContainer = div({ class: 'game-list-item__timestamps' });
    const lastSavedText = div(
      { class: 'game-list-item__timestamp game-list-item__timestamp--highlight' },
      `⏰ ${this.formatRelativeTime(lastSaved)}`
    );
    const createdText = div(
      { class: 'game-list-item__timestamp' },
      `Created: ${this.formatDate(createdAt)}`
    );
    timestampsContainer.appendChild(lastSavedText);
    timestampsContainer.appendChild(createdText);

    // Actions section
    const actionsContainer = div({ class: 'game-list-item__actions' });

    const loadButton = button('Load Game', {
      class: 'game-list-item__button game-list-item__button--primary',
      onclick: () => this.handleLoad(),
    });

    const deleteButton = button('Delete', {
      class: 'game-list-item__button game-list-item__button--danger',
      onclick: () => this.handleDelete(),
    });

    actionsContainer.appendChild(loadButton);
    actionsContainer.appendChild(deleteButton);

    // Assemble card
    card.appendChild(scenarioTitle);
    card.appendChild(characterInfo);
    card.appendChild(timestampsContainer);
    card.appendChild(actionsContainer);

    return card;
  }

  private handleLoad(): void {
    this.props.onLoad(this.props.gameId);
  }

  private handleDelete(): void {
    const confirmed = confirm(
      `Are you sure you want to delete this game?\n\nScenario: ${this.props.scenarioName}\nCharacter: ${this.props.characterName}`
    );

    if (confirmed) {
      this.props.onDelete(this.props.gameId);
    }
  }

  private formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  }

  /**
   * Format last saved time as human-readable relative time
   * Examples: "2 days ago", "5 hours ago", "Recently"
   */
  private formatRelativeTime(dateString: string): string {
    try {
      const lastSaved = new Date(dateString);
      const now = new Date();
      const timeDiff = now.getTime() - lastSaved.getTime();
      const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));
      const daysAgo = Math.floor(timeDiff / (1000 * 60 * 60 * 24));

      if (daysAgo > 0) {
        return `${daysAgo} day${daysAgo > 1 ? 's' : ''} ago`;
      } else if (hoursAgo > 0) {
        return `${hoursAgo} hour${hoursAgo > 1 ? 's' : ''} ago`;
      } else {
        return 'Recently';
      }
    } catch {
      return this.formatDate(dateString);
    }
  }
}
