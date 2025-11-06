/**
 * JournalEntryModal Component
 *
 * Modal for creating or editing journal entries.
 * Uses backend PlayerJournalEntry structure (content + tags only).
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { PlayerJournalEntry } from '../../types/generated/PlayerJournalEntry.js';

export interface JournalEntryModalProps {
  entry?: PlayerJournalEntry;
  onSave: (data: EntryFormData) => void;
  onCancel: () => void;
}

export interface EntryFormData {
  content: string;
  tags: string[];
}

/**
 * Journal entry modal component
 */
export class JournalEntryModal extends Component<JournalEntryModalProps> {
  private contentTextarea: HTMLTextAreaElement | null = null;
  private tagsInput: HTMLInputElement | null = null;

  constructor(props: JournalEntryModalProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const overlay = div({ class: 'modal-overlay' });

    const modal = div({ class: 'journal-entry-modal' });

    // Header
    const header = div({ class: 'journal-entry-modal__header' });
    const title = div(
      { class: 'journal-entry-modal__title' },
      this.props.entry ? 'Edit Journal Entry' : 'New Journal Entry'
    );

    const closeButton = button('✕', {
      class: 'journal-entry-modal__close-btn',
      onclick: () => this.props.onCancel(),
    });

    header.appendChild(title);
    header.appendChild(closeButton);

    // Form
    const form = div({ class: 'journal-entry-modal__form' });

    // Content textarea
    const contentField = this.createContentField();
    form.appendChild(contentField);

    // Tags input
    const tagsField = this.createTagsField();
    form.appendChild(tagsField);

    // Footer with action buttons
    const footer = div({ class: 'journal-entry-modal__footer' });

    const cancelButton = button('Cancel', {
      class: 'journal-entry-modal__button journal-entry-modal__button--cancel',
      onclick: () => this.props.onCancel(),
    });

    const saveButton = button('Save', {
      class: 'journal-entry-modal__button journal-entry-modal__button--save',
      onclick: () => this.handleSave(),
    });

    footer.appendChild(cancelButton);
    footer.appendChild(saveButton);

    // Assemble modal
    modal.appendChild(header);
    modal.appendChild(form);
    modal.appendChild(footer);

    overlay.appendChild(modal);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        this.props.onCancel();
      }
    });

    return overlay;
  }

  private createContentField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Content:';

    this.contentTextarea = document.createElement('textarea');
    this.contentTextarea.className = 'journal-entry-modal__textarea';
    this.contentTextarea.placeholder = 'Write your journal entry here...';
    this.contentTextarea.rows = 12;
    this.contentTextarea.value = this.props.entry?.content || '';
    this.contentTextarea.required = true;

    field.appendChild(label);
    field.appendChild(this.contentTextarea);

    return field;
  }

  private createTagsField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Tags (comma-separated):';

    this.tagsInput = document.createElement('input');
    this.tagsInput.type = 'text';
    this.tagsInput.className = 'journal-entry-modal__input';
    this.tagsInput.placeholder = 'combat, important, quest-related';
    this.tagsInput.value = this.props.entry?.tags?.join(', ') || '';

    const helpText = div(
      { class: 'journal-entry-modal__help-text' },
      'Tags will be normalized to lowercase with dashes. Only letters, numbers, dashes, underscores, and colons allowed.'
    );

    field.appendChild(label);
    field.appendChild(this.tagsInput);
    field.appendChild(helpText);

    return field;
  }

  private handleSave(): void {
    if (!this.contentTextarea || !this.tagsInput) {
      return;
    }

    const content = this.contentTextarea.value.trim();

    // Validation
    if (!content) {
      alert('Please enter content');
      this.contentTextarea.focus();
      return;
    }

    // Parse tags from comma-separated input
    const tagsText = this.tagsInput.value.trim();
    const tags = tagsText
      ? tagsText.split(',').map(t => t.trim()).filter(t => t.length > 0)
      : [];

    // Call save callback
    this.props.onSave({
      content,
      tags,
    });
  }
}
