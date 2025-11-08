/**
 * Tests for UI Builder Utilities
 */

import { describe, it, expect, vi } from 'vitest';
import {
  createHeader,
  createSection,
  createCard,
  createStatBar,
  createBadge,
  createIconButton,
  createEmptyState,
  type BadgeVariant,
} from '../ui-builders.js';

describe('createHeader', () => {
  it('should create header with title', () => {
    const header = createHeader('Test Title');

    expect(header.classList.contains('component__header')).toBe(true);
    expect(header.textContent).toContain('Test Title');
  });

  it('should create header with custom className', () => {
    const header = createHeader('Test', { className: 'custom-header' });

    expect(header.classList.contains('custom-header')).toBe(true);
  });

  it('should create header with subtitle', () => {
    const header = createHeader('Title', { subtitle: '3/4' });

    expect(header.textContent).toContain('Title');
    expect(header.textContent).toContain('3/4');
  });

  it('should create header with action buttons', () => {
    const button1 = document.createElement('button');
    button1.textContent = 'Action 1';
    const button2 = document.createElement('button');
    button2.textContent = 'Action 2';

    const header = createHeader('Title', { actions: [button1, button2] });

    const actionsContainer = header.querySelector('.component__header__actions');
    expect(actionsContainer).not.toBeNull();
    expect(actionsContainer?.children.length).toBe(2);
  });

  it('should create header with all options', () => {
    const action = document.createElement('button');
    const header = createHeader('Title', {
      className: 'my-header',
      subtitle: 'Subtitle',
      actions: [action],
    });

    expect(header.classList.contains('my-header')).toBe(true);
    expect(header.textContent).toContain('Title');
    expect(header.textContent).toContain('Subtitle');
    expect(header.querySelector('.my-header__actions')).not.toBeNull();
  });
});

describe('createSection', () => {
  it('should create section with title and content', () => {
    const content = document.createElement('div');
    content.textContent = 'Section content';

    const section = createSection('Section Title', content);

    expect(section.classList.contains('section')).toBe(true);
    expect(section.textContent).toContain('Section Title');
    expect(section.textContent).toContain('Section content');
  });

  it('should create section without title', () => {
    const content = document.createElement('div');
    content.textContent = 'Content';

    const section = createSection(null, content);

    expect(section.querySelector('.section__header')).toBeNull();
    expect(section.textContent).toBe('Content');
  });

  it('should create collapsible section', () => {
    const content = document.createElement('div');
    const section = createSection('Title', content, { collapsible: true });

    const header = section.querySelector('.section__header');
    expect(header?.classList.contains('section__header--collapsible')).toBe(true);

    const icon = section.querySelector('.section__toggle-icon');
    expect(icon?.textContent).toBe('▼'); // Expanded by default
  });

  it('should create collapsed section', () => {
    const content = document.createElement('div');
    const section = createSection('Title', content, {
      collapsible: true,
      collapsed: true,
    });

    const icon = section.querySelector('.section__toggle-icon');
    expect(icon?.textContent).toBe('▶'); // Collapsed
    expect(content.classList.contains('section__content--collapsed')).toBe(true);
  });

  it('should toggle section when header is clicked', () => {
    const content = document.createElement('div');
    const onToggle = vi.fn();

    const section = createSection('Title', content, {
      collapsible: true,
      onToggle,
    });

    const header = section.querySelector('.section__header') as HTMLElement;
    const icon = section.querySelector('.section__toggle-icon') as HTMLElement;

    // Initially expanded
    expect(icon.textContent).toBe('▼');
    expect(onToggle).not.toHaveBeenCalled();

    // Click to collapse
    header.click();
    expect(icon.textContent).toBe('▶');
    expect(content.classList.contains('section__content--collapsed')).toBe(true);
    expect(onToggle).toHaveBeenCalledWith(true);

    // Click to expand
    header.click();
    expect(icon.textContent).toBe('▼');
    expect(content.classList.contains('section__content--collapsed')).toBe(false);
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it('should use custom className', () => {
    const content = document.createElement('div');
    const section = createSection('Title', content, { className: 'custom-section' });

    expect(section.classList.contains('custom-section')).toBe(true);
  });
});

describe('createCard', () => {
  it('should create basic card with content', () => {
    const content = document.createElement('div');
    content.textContent = 'Card content';

    const card = createCard(content);

    expect(card.classList.contains('card')).toBe(true);
    expect(card.textContent).toContain('Card content');
  });

  it('should create card with header', () => {
    const content = document.createElement('div');
    const card = createCard(content, { header: 'Card Header' });

    expect(card.textContent).toContain('Card Header');
    expect(card.querySelector('.card__header')).not.toBeNull();
  });

  it('should create card with footer', () => {
    const content = document.createElement('div');
    const footer = document.createElement('div');
    footer.textContent = 'Footer content';

    const card = createCard(content, { footer });

    expect(card.textContent).toContain('Footer content');
    expect(card.querySelector('.card__footer')).not.toBeNull();
  });

  it('should create hoverable card', () => {
    const content = document.createElement('div');
    const card = createCard(content, { hoverable: true });

    expect(card.classList.contains('card--hoverable')).toBe(true);
  });

  it('should create selected card', () => {
    const content = document.createElement('div');
    const card = createCard(content, { selected: true });

    expect(card.classList.contains('card--selected')).toBe(true);
  });

  it('should create clickable card with onClick handler', () => {
    const content = document.createElement('div');
    const onClick = vi.fn();

    const card = createCard(content, { onClick });

    expect(card.classList.contains('card--clickable')).toBe(true);

    card.click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should create card with all options', () => {
    const content = document.createElement('div');
    const footer = document.createElement('div');
    const onClick = vi.fn();

    const card = createCard(content, {
      className: 'custom-card',
      header: 'Header',
      footer,
      onClick,
      hoverable: true,
      selected: true,
    });

    expect(card.classList.contains('custom-card')).toBe(true);
    expect(card.classList.contains('custom-card--hoverable')).toBe(true);
    expect(card.classList.contains('custom-card--selected')).toBe(true);
    expect(card.classList.contains('custom-card--clickable')).toBe(true);
    expect(card.textContent).toContain('Header');

    card.click();
    expect(onClick).toHaveBeenCalled();
  });
});

describe('createStatBar', () => {
  it('should create stat bar with label and values', () => {
    const bar = createStatBar('HP', 45, 50);

    expect(bar.classList.contains('stat-bar')).toBe(true);
    expect(bar.textContent).toContain('HP');
    expect(bar.textContent).toContain('45/50');
  });

  it('should calculate percentage correctly', () => {
    const bar = createStatBar('HP', 25, 100);
    const fill = bar.querySelector('.stat-bar__fill') as HTMLElement;

    expect(fill.style.width).toBe('25%');
  });

  it('should add danger class when <= 25%', () => {
    const bar = createStatBar('HP', 25, 100);
    const fill = bar.querySelector('.stat-bar__fill');

    expect(fill?.classList.contains('stat-bar__fill--danger')).toBe(true);
  });

  it('should add warning class when <= 50%', () => {
    const bar = createStatBar('HP', 40, 100);
    const fill = bar.querySelector('.stat-bar__fill');

    expect(fill?.classList.contains('stat-bar__fill--warning')).toBe(true);
  });

  it('should not add warning/danger class when > 50%', () => {
    const bar = createStatBar('HP', 75, 100);
    const fill = bar.querySelector('.stat-bar__fill');

    expect(fill?.classList.contains('stat-bar__fill--danger')).toBe(false);
    expect(fill?.classList.contains('stat-bar__fill--warning')).toBe(false);
  });

  it('should handle 0 max value', () => {
    const bar = createStatBar('HP', 0, 0);
    const fill = bar.querySelector('.stat-bar__fill') as HTMLElement;

    expect(fill.style.width).toBe('0%');
  });

  it('should clamp percentage to 0-100%', () => {
    const barOver = createStatBar('HP', 150, 100);
    const fillOver = barOver.querySelector('.stat-bar__fill') as HTMLElement;
    expect(fillOver.style.width).toBe('100%');

    const barUnder = createStatBar('HP', -10, 100);
    const fillUnder = barUnder.querySelector('.stat-bar__fill') as HTMLElement;
    expect(fillUnder.style.width).toBe('0%');
  });

  it('should use variant class', () => {
    const bar = createStatBar('MP', 30, 50, { variant: 'mp' });

    expect(bar.classList.contains('stat-bar--mp')).toBe(true);
  });

  it('should hide value when showValue is false', () => {
    const bar = createStatBar('XP', 500, 1000, { showValue: false });

    expect(bar.querySelector('.stat-bar__value')).toBeNull();
  });

  it('should use custom className', () => {
    const bar = createStatBar('HP', 45, 50, { className: 'custom-bar' });

    expect(bar.classList.contains('custom-bar')).toBe(true);
  });
});

describe('createBadge', () => {
  it('should create badge with text', () => {
    const badge = createBadge('WORLD');

    expect(badge.classList.contains('badge')).toBe(true);
    expect(badge.textContent).toBe('WORLD');
  });

  it('should create badge with default variant (info)', () => {
    const badge = createBadge('Test');

    expect(badge.classList.contains('badge--info')).toBe(true);
  });

  it('should create badge with custom variant', () => {
    const variants: BadgeVariant[] = [
      'world',
      'location',
      'npc',
      'player',
      'info',
      'success',
      'warning',
      'danger',
    ];

    variants.forEach((variant) => {
      const badge = createBadge('Test', variant);
      expect(badge.classList.contains(`badge--${variant}`)).toBe(true);
    });
  });
});

describe('createIconButton', () => {
  it('should create icon button with click handler', () => {
    const onClick = vi.fn();
    const btn = createIconButton('✏️', onClick);

    expect(btn.tagName).toBe('BUTTON');
    expect(btn.textContent).toBe('✏️');
    expect(btn.classList.contains('btn-icon')).toBe(true);

    // Dispatch click event (jsdom requires explicit event dispatch)
    btn.dispatchEvent(new Event('click'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should use default variant (ghost)', () => {
    const btn = createIconButton('✏️', vi.fn());

    expect(btn.classList.contains('btn-icon--ghost')).toBe(true);
  });

  it('should use custom variant', () => {
    const btn = createIconButton('✏️', vi.fn(), { variant: 'danger' });

    expect(btn.classList.contains('btn-icon--danger')).toBe(true);
  });

  it('should set aria-label', () => {
    const btn = createIconButton('✏️', vi.fn(), { ariaLabel: 'Edit entry' });

    expect(btn.getAttribute('aria-label')).toBe('Edit entry');
  });

  it('should set title attribute', () => {
    const btn = createIconButton('✏️', vi.fn(), { title: 'Edit' });

    expect(btn.getAttribute('title')).toBe('Edit');
  });

  it('should create disabled button', () => {
    const btn = createIconButton('✏️', vi.fn(), { disabled: true });

    expect(btn.hasAttribute('disabled')).toBe(true);
  });

  it('should use custom className', () => {
    const btn = createIconButton('✏️', vi.fn(), { className: 'custom-btn' });

    expect(btn.classList.contains('custom-btn')).toBe(true);
  });
});

describe('createEmptyState', () => {
  it('should create empty state with message', () => {
    const emptyState = createEmptyState('No items found');

    expect(emptyState.classList.contains('empty-state')).toBe(true);
    expect(emptyState.textContent).toContain('No items found');
  });

  it('should create empty state with icon', () => {
    const emptyState = createEmptyState('No members', { icon: '👥' });

    const icon = emptyState.querySelector('.empty-state__icon');
    expect(icon?.textContent).toBe('👥');
  });

  it('should create empty state with action button', () => {
    const onClick = vi.fn();
    const emptyState = createEmptyState('No items', {
      action: {
        label: 'Add Item',
        onClick,
      },
    });

    const actionBtn = emptyState.querySelector('.empty-state__action') as HTMLButtonElement;
    expect(actionBtn).not.toBeNull();
    expect(actionBtn.textContent).toBe('Add Item');

    actionBtn.click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should create empty state with all options', () => {
    const onClick = vi.fn();
    const emptyState = createEmptyState('No data', {
      className: 'custom-empty',
      icon: '📊',
      action: {
        label: 'Load Data',
        onClick,
      },
    });

    expect(emptyState.classList.contains('custom-empty')).toBe(true);
    expect(emptyState.textContent).toContain('📊');
    expect(emptyState.textContent).toContain('No data');
    expect(emptyState.textContent).toContain('Load Data');
  });

  it('should work without icon or action', () => {
    const emptyState = createEmptyState('Empty');

    expect(emptyState.querySelector('.empty-state__icon')).toBeNull();
    expect(emptyState.querySelector('.empty-state__action')).toBeNull();
    expect(emptyState.textContent).toBe('Empty');
  });
});
