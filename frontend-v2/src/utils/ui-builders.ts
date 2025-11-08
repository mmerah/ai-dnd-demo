/**
 * UI Builder Utilities
 *
 * Reusable functions for building common UI patterns.
 * Extracted from components to follow DRY principle.
 *
 * All builders return HTMLElements that can be composed and styled using BEM classes.
 */

import { createElement, div, span, button } from './dom.js';

/**
 * Options for creating a header
 */
export interface HeaderOptions {
  /** Additional CSS class for the header container */
  className?: string;
  /** Optional subtitle or metadata */
  subtitle?: string;
  /** Optional action buttons to append to header */
  actions?: HTMLElement[];
}

/**
 * Creates a standard header with title
 * @param title - Header title text
 * @param options - Configuration options
 * @returns HTMLElement with header structure
 * @example
 * ```ts
 * const header = createHeader('Party Members', {
 *   subtitle: '3/4',
 *   className: 'party-panel__header'
 * });
 * ```
 */
export function createHeader(title: string, options: HeaderOptions = {}): HTMLElement {
  const { className = 'component__header', subtitle, actions } = options;

  const header = div({ class: className });

  const titleRow = div({ class: `${className}__title-row` });
  const titleEl = createElement('h2', { class: `${className}__title` });
  titleEl.textContent = title;
  titleRow.appendChild(titleEl);

  if (subtitle) {
    const subtitleEl = span({ class: `${className}__subtitle` });
    subtitleEl.textContent = subtitle;
    titleRow.appendChild(subtitleEl);
  }

  header.appendChild(titleRow);

  if (actions && actions.length > 0) {
    const actionsContainer = div({ class: `${className}__actions` });
    actions.forEach((action) => actionsContainer.appendChild(action));
    header.appendChild(actionsContainer);
  }

  return header;
}

/**
 * Options for creating a section
 */
export interface SectionOptions {
  /** Additional CSS class for the section container */
  className?: string;
  /** Whether the section should be collapsible */
  collapsible?: boolean;
  /** Whether the section starts collapsed (requires collapsible: true) */
  collapsed?: boolean;
  /** Callback when section is toggled (requires collapsible: true) */
  onToggle?: (collapsed: boolean) => void;
}

/**
 * Creates a section with optional title and collapsible behavior
 * @param title - Section title (optional)
 * @param content - Content to display in the section
 * @param options - Configuration options
 * @returns HTMLElement with section structure
 * @example
 * ```ts
 * const content = div({}, 'Section content here');
 * const section = createSection('Features', content, {
 *   collapsible: true,
 *   collapsed: false
 * });
 * ```
 */
export function createSection(
  title: string | null,
  content: HTMLElement,
  options: SectionOptions = {}
): HTMLElement {
  const { className = 'section', collapsible = false, collapsed = false, onToggle } = options;

  const section = div({ class: className });

  if (title) {
    const headerEl = div({ class: `${className}__header` });
    const titleEl = createElement('h3', { class: `${className}__title` });
    titleEl.textContent = title;

    if (collapsible) {
      const icon = span({ class: `${className}__toggle-icon` });
      icon.textContent = collapsed ? '▶' : '▼';
      headerEl.appendChild(icon);

      headerEl.classList.add(`${className}__header--collapsible`);
      headerEl.addEventListener('click', () => {
        const isCollapsed = content.classList.toggle(`${className}__content--collapsed`);
        icon.textContent = isCollapsed ? '▶' : '▼';
        if (onToggle) {
          onToggle(isCollapsed);
        }
      });
    }

    headerEl.appendChild(titleEl);
    section.appendChild(headerEl);

    if (collapsed) {
      content.classList.add(`${className}__content--collapsed`);
    }
  }

  content.classList.add(`${className}__content`);
  section.appendChild(content);

  return section;
}

/**
 * Options for creating a card
 */
export interface CardOptions {
  /** Additional CSS class for the card container */
  className?: string;
  /** Card header text (optional) */
  header?: string;
  /** Card footer element (optional) */
  footer?: HTMLElement;
  /** Click handler for the entire card */
  onClick?: () => void;
  /** Whether the card should have hover effects */
  hoverable?: boolean;
  /** Whether the card is currently selected */
  selected?: boolean;
}

/**
 * Creates a card container with consistent styling
 * @param content - Content to display in the card
 * @param options - Configuration options
 * @returns HTMLElement with card structure
 * @example
 * ```ts
 * const content = div({}, 'Card content');
 * const card = createCard(content, {
 *   header: 'Card Title',
 *   hoverable: true,
 *   onClick: () => console.log('Card clicked')
 * });
 * ```
 */
export function createCard(content: HTMLElement, options: CardOptions = {}): HTMLElement {
  const {
    className = 'card',
    header,
    footer,
    onClick,
    hoverable = false,
    selected = false,
  } = options;

  const card = div({ class: className });

  if (hoverable) {
    card.classList.add(`${className}--hoverable`);
  }

  if (selected) {
    card.classList.add(`${className}--selected`);
  }

  if (onClick) {
    card.classList.add(`${className}--clickable`);
    card.addEventListener('click', onClick);
  }

  if (header) {
    const headerEl = div({ class: `${className}__header` });
    headerEl.textContent = header;
    card.appendChild(headerEl);
  }

  content.classList.add(`${className}__content`);
  card.appendChild(content);

  if (footer) {
    footer.classList.add(`${className}__footer`);
    card.appendChild(footer);
  }

  return card;
}

/**
 * Options for creating a stat bar
 */
export interface StatBarOptions {
  /** Additional CSS class for the bar container */
  className?: string;
  /** Color variant for the bar */
  variant?: 'hp' | 'mp' | 'xp' | 'default';
  /** Whether to show the numeric value */
  showValue?: boolean;
}

/**
 * Creates a stat bar (e.g., HP, MP, XP)
 * @param label - Label for the stat
 * @param current - Current value
 * @param max - Maximum value
 * @param options - Configuration options
 * @returns HTMLElement with stat bar structure
 * @example
 * ```ts
 * const hpBar = createStatBar('HP', 45, 50, { variant: 'hp', showValue: true });
 * ```
 */
export function createStatBar(
  label: string,
  current: number,
  max: number,
  options: StatBarOptions = {}
): HTMLElement {
  const { className = 'stat-bar', variant = 'default', showValue = true } = options;

  const container = div({ class: className });
  if (variant !== 'default') {
    container.classList.add(`${className}--${variant}`);
  }

  // Label
  const labelEl = span({ class: `${className}__label` });
  labelEl.textContent = label;
  container.appendChild(labelEl);

  // Bar track
  const track = div({ class: `${className}__track` });
  const fill = div({ class: `${className}__fill` });

  const percentage = max > 0 ? Math.min(Math.max((current / max) * 100, 0), 100) : 0;
  fill.style.width = `${percentage}%`;

  // Add warning/danger classes based on percentage
  if (percentage <= 25) {
    fill.classList.add(`${className}__fill--danger`);
  } else if (percentage <= 50) {
    fill.classList.add(`${className}__fill--warning`);
  }

  track.appendChild(fill);
  container.appendChild(track);

  // Value text
  if (showValue) {
    const valueEl = span({ class: `${className}__value` });
    valueEl.textContent = `${current}/${max}`;
    container.appendChild(valueEl);
  }

  return container;
}

/**
 * Badge variant types
 */
export type BadgeVariant = 'world' | 'location' | 'npc' | 'player' | 'info' | 'success' | 'warning' | 'danger';

/**
 * Creates a colored badge
 * @param text - Badge text
 * @param variant - Visual variant for the badge
 * @returns HTMLElement with badge styling
 * @example
 * ```ts
 * const badge = createBadge('WORLD', 'world');
 * const dangerBadge = createBadge('Critical', 'danger');
 * ```
 */
export function createBadge(text: string, variant: BadgeVariant = 'info'): HTMLElement {
  const badge = span({ class: 'badge' });
  badge.classList.add(`badge--${variant}`);
  badge.textContent = text;
  return badge;
}

/**
 * Options for creating an icon button
 */
export interface IconButtonOptions {
  /** Additional CSS class for the button */
  className?: string;
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  /** Accessible label for screen readers */
  ariaLabel?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
  /** Tooltip text */
  title?: string;
}

/**
 * Creates an icon-only button
 * @param icon - Icon text/emoji or HTML
 * @param onClick - Click handler
 * @param options - Configuration options
 * @returns HTMLElement button
 * @example
 * ```ts
 * const editBtn = createIconButton('✏️', () => handleEdit(), {
 *   ariaLabel: 'Edit entry',
 *   variant: 'ghost'
 * });
 * ```
 */
export function createIconButton(
  icon: string,
  onClick: () => void,
  options: IconButtonOptions = {}
): HTMLElement {
  const {
    className = 'btn-icon',
    variant = 'ghost',
    ariaLabel,
    disabled = false,
    title,
  } = options;

  const btn = createElement('button', {
    class: className,
    disabled,
  }) as HTMLButtonElement;

  // Add click handler directly (not via attributes)
  btn.addEventListener('click', onClick);

  btn.classList.add(`${className}--${variant}`);

  if (ariaLabel) {
    btn.setAttribute('aria-label', ariaLabel);
  }

  if (title) {
    btn.setAttribute('title', title);
  }

  btn.textContent = icon;

  return btn;
}

/**
 * Options for creating an empty state
 */
export interface EmptyStateOptions {
  /** Additional CSS class for the container */
  className?: string;
  /** Icon or emoji to display */
  icon?: string;
  /** Call-to-action button */
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Creates an empty state placeholder
 * @param message - Message to display
 * @param options - Configuration options
 * @returns HTMLElement with empty state structure
 * @example
 * ```ts
 * const emptyState = createEmptyState('No party members yet', {
 *   icon: '👥',
 *   action: {
 *     label: 'Add Member',
 *     onClick: () => handleAddMember()
 *   }
 * });
 * ```
 */
export function createEmptyState(message: string, options: EmptyStateOptions = {}): HTMLElement {
  const { className = 'empty-state', icon, action } = options;

  const container = div({ class: className });

  if (icon) {
    const iconEl = div({ class: `${className}__icon` });
    iconEl.textContent = icon;
    container.appendChild(iconEl);
  }

  const messageEl = div({ class: `${className}__message` });
  messageEl.textContent = message;
  container.appendChild(messageEl);

  if (action) {
    const actionBtn = button(action.label, {
      class: `${className}__action btn btn--primary`,
      onclick: action.onClick,
    });
    container.appendChild(actionBtn);
  }

  return container;
}
