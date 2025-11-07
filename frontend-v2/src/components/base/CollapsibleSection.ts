/**
 * CollapsibleSection Component
 *
 * A reusable collapsible section with header and content.
 * Follows the pattern from old frontend for consistency.
 *
 * Usage:
 * const section = new CollapsibleSection({
 *   title: 'Abilities',
 *   initiallyCollapsed: false,
 *   children: [abilityGrid]
 * });
 */

import { Component } from './Component.js';
import { div } from '../../utils/dom.js';

export interface CollapsibleSectionProps {
  /**
   * Section title displayed in the header
   */
  title: string;

  /**
   * Whether the section starts collapsed
   * @default false
   */
  initiallyCollapsed?: boolean;

  /**
   * Child elements to display in the collapsible content
   */
  children: HTMLElement[];

  /**
   * Optional CSS class for the container
   */
  className?: string;
}

/**
 * Collapsible section component with toggle functionality
 */
export class CollapsibleSection extends Component<CollapsibleSectionProps> {
  private isCollapsed: boolean;
  private contentElement: HTMLElement | null = null;
  private toggleElement: HTMLElement | null = null;
  private headerElement: HTMLElement | null = null;

  constructor(props: CollapsibleSectionProps) {
    super(props);
    this.isCollapsed = props.initiallyCollapsed ?? false;
  }

  /**
   * Bound click handler for header toggle
   * Stored as class property for proper cleanup
   */
  private handleHeaderClick = (): void => {
    this.toggle();
  };

  protected render(): HTMLElement {
    const classes = ['collapsible'];
    if (this.props.className) {
      classes.push(this.props.className);
    }
    if (this.isCollapsed) {
      classes.push('collapsed');
    }

    const container = div({ class: classes.join(' ') });

    // Header (clickable)
    this.headerElement = div({ class: 'collapsible-header' });

    const titleText = document.createElement('h3');
    titleText.textContent = this.props.title;
    titleText.style.margin = '0';
    titleText.style.flex = '1';

    this.toggleElement = div({ class: 'toggle' }, '▼');

    this.headerElement.appendChild(titleText);
    this.headerElement.appendChild(this.toggleElement);

    // Click handler for toggle - using bound method for proper cleanup
    this.headerElement.addEventListener('click', this.handleHeaderClick);

    // Content (collapsible)
    this.contentElement = div({ class: 'collapsible-content' });
    for (const child of this.props.children) {
      this.contentElement.appendChild(child);
    }

    container.appendChild(this.headerElement);
    container.appendChild(this.contentElement);

    return container;
  }

  /**
   * Toggle collapsed state
   */
  public toggle(): void {
    this.isCollapsed = !this.isCollapsed;

    if (!this.element || !this.contentElement || !this.toggleElement) {
      console.warn('[CollapsibleSection] Cannot toggle - elements not initialized');
      return;
    }

    // Update classes and visibility
    if (this.isCollapsed) {
      this.element.classList.add('collapsed');
      this.contentElement.style.display = 'none';
      this.toggleElement.style.transform = 'rotate(-90deg)';
    } else {
      this.element.classList.remove('collapsed');
      this.contentElement.style.display = 'block';
      this.toggleElement.style.transform = 'rotate(0deg)';
    }

    console.log(`[CollapsibleSection] Toggled "${this.props.title}": ${this.isCollapsed ? 'collapsed' : 'expanded'}`);
  }

  /**
   * Programmatically collapse the section
   */
  public collapse(): void {
    if (!this.isCollapsed) {
      this.toggle();
    }
  }

  /**
   * Programmatically expand the section
   */
  public expand(): void {
    if (this.isCollapsed) {
      this.toggle();
    }
  }

  /**
   * Get current collapsed state
   */
  public getIsCollapsed(): boolean {
    return this.isCollapsed;
  }

  /**
   * Cleanup event listeners on unmount to prevent memory leaks
   */
  override onUnmount(): void {
    if (this.headerElement) {
      this.headerElement.removeEventListener('click', this.handleHeaderClick);
    }
    super.onUnmount();
  }
}
