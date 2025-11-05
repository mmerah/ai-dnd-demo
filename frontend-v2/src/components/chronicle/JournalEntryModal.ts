/**
 * JournalEntryModal Component
 *
 * Modal for creating or editing journal entries.
 */

import { Component } from '../base/Component.js';
import { div, button } from '../../utils/dom.js';
import type { JournalEntry } from '../../services/api/JournalApiService.js';

export interface JournalEntryModalProps {
  entry?: JournalEntry; // If provided, we're editing; otherwise creating
  locations: string[];
  onSave: (data: EntryFormData) => void;
  onCancel: () => void;
}

export interface EntryFormData {
  title: string;
  content: string;
  category: 'Event' | 'NPC' | 'Location' | 'Quest' | 'Item';
  location?: string;
}

/**
 * Journal entry modal component
 */
export class JournalEntryModal extends Component<JournalEntryModalProps> {
  private titleInput: HTMLInputElement | null = null;
  private contentTextarea: HTMLTextAreaElement | null = null;
  private categorySelect: HTMLSelectElement | null = null;
  private locationSelect: HTMLSelectElement | null = null;

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

    // Title input
    const titleField = this.createTitleField();
    form.appendChild(titleField);

    // Category select
    const categoryField = this.createCategoryField();
    form.appendChild(categoryField);

    // Location select
    const locationField = this.createLocationField();
    form.appendChild(locationField);

    // Content textarea
    const contentField = this.createContentField();
    form.appendChild(contentField);

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

  private createTitleField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Title:';

    this.titleInput = document.createElement('input');
    this.titleInput.type = 'text';
    this.titleInput.className = 'journal-entry-modal__input';
    this.titleInput.placeholder = 'Entry title...';
    this.titleInput.value = this.props.entry?.title || '';
    this.titleInput.required = true;

    field.appendChild(label);
    field.appendChild(this.titleInput);

    return field;
  }

  private createCategoryField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Category:';

    this.categorySelect = document.createElement('select');
    this.categorySelect.className = 'journal-entry-modal__select';

    const categories: Array<'Event' | 'NPC' | 'Location' | 'Quest' | 'Item'> = [
      'Event',
      'NPC',
      'Location',
      'Quest',
      'Item',
    ];

    categories.forEach((category) => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      if (category === this.props.entry?.category) {
        option.selected = true;
      }
      this.categorySelect!.appendChild(option);
    });

    field.appendChild(label);
    field.appendChild(this.categorySelect);

    return field;
  }

  private createLocationField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Location (optional):';

    this.locationSelect = document.createElement('select');
    this.locationSelect.className = 'journal-entry-modal__select';

    // Add empty option
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '-- None --';
    this.locationSelect.appendChild(emptyOption);

    // Add location options
    this.props.locations.forEach((location) => {
      const option = document.createElement('option');
      option.value = location;
      option.textContent = location;
      if (location === this.props.entry?.location) {
        option.selected = true;
      }
      this.locationSelect!.appendChild(option);
    });

    field.appendChild(label);
    field.appendChild(this.locationSelect);

    return field;
  }

  private createContentField(): HTMLElement {
    const field = div({ class: 'journal-entry-modal__field' });

    const label = document.createElement('label');
    label.className = 'journal-entry-modal__label';
    label.textContent = 'Content:';

    this.contentTextarea = document.createElement('textarea');
    this.contentTextarea.className = 'journal-entry-modal__textarea';
    this.contentTextarea.placeholder = 'Write your journal entry here...';
    this.contentTextarea.rows = 10;
    this.contentTextarea.value = this.props.entry?.content || '';
    this.contentTextarea.required = true;

    field.appendChild(label);
    field.appendChild(this.contentTextarea);

    return field;
  }

  private handleSave(): void {
    if (!this.titleInput || !this.contentTextarea || !this.categorySelect) {
      return;
    }

    const title = this.titleInput.value.trim();
    const content = this.contentTextarea.value.trim();
    const category = this.categorySelect.value as
      | 'Event'
      | 'NPC'
      | 'Location'
      | 'Quest'
      | 'Item';
    const location = this.locationSelect?.value || undefined;

    // Validation
    if (!title) {
      alert('Please enter a title');
      this.titleInput.focus();
      return;
    }

    if (!content) {
      alert('Please enter content');
      this.contentTextarea.focus();
      return;
    }

    // Call save callback
    this.props.onSave({
      title,
      content,
      category,
      location,
    });
  }
}
