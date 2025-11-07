/**
 * Modal Component
 *
 * Provides a customizable modal dialog system with promise-based API.
 * Replaces native browser dialogs (alert, confirm) with styled modals.
 *
 * Usage:
 * const confirmed = await Modal.confirm('Are you sure?', 'Delete Item');
 * if (confirmed) {
 *   // User clicked confirm
 * }
 */

import { div, button, createElement } from '../../utils/dom.js';

export interface ModalButton {
  text: string;
  onClick: () => void;
  primary?: boolean;
  danger?: boolean;
}

export interface ModalOptions {
  title: string;
  message: string;
  buttons: ModalButton[];
}

/**
 * Modal dialog component with overlay
 */
export class Modal {
  private overlay: HTMLElement | null = null;
  private modal: HTMLElement | null = null;
  private resolveCallback: ((value: boolean) => void) | null = null;

  constructor(private options: ModalOptions) {}

  /**
   * Show the modal and return a promise that resolves when user interacts
   */
  public show(): Promise<boolean> {
    return new Promise((resolve) => {
      this.resolveCallback = resolve;
      this.render();
      this.mount();
    });
  }

  private render(): void {
    // Overlay (darkens background and blocks interaction)
    this.overlay = div({ class: 'modal-overlay' });

    // Modal container
    this.modal = div({ class: 'modal' });

    // Header
    const header = div({ class: 'modal__header' });
    const title = createElement('h2', { class: 'modal__title' });
    title.textContent = this.options.title;
    header.appendChild(title);

    // Body
    const body = div({ class: 'modal__body' });
    const message = createElement('p', { class: 'modal__message' });
    message.textContent = this.options.message;
    body.appendChild(message);

    // Footer with buttons
    const footer = div({ class: 'modal__footer' });
    for (const btnConfig of this.options.buttons) {
      const btn = this.createButton(btnConfig);
      footer.appendChild(btn);
    }

    this.modal.appendChild(header);
    this.modal.appendChild(body);
    this.modal.appendChild(footer);

    this.overlay.appendChild(this.modal);

    // Click overlay to dismiss (as cancel)
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close(false);
      }
    });

    // ESC key to dismiss
    document.addEventListener('keydown', this.handleEscKey);
  }

  private createButton(config: ModalButton): HTMLElement {
    const classes = ['modal__button'];

    if (config.primary) {
      classes.push('modal__button--primary');
    }
    if (config.danger) {
      classes.push('modal__button--danger');
    }

    const btn = button(config.text, {
      class: classes.join(' '),
      onclick: () => {
        config.onClick();
      },
    });

    return btn;
  }

  private handleEscKey = (e: KeyboardEvent): void => {
    if (e.key === 'Escape') {
      this.close(false);
    }
  };

  private mount(): void {
    if (!this.overlay) return;
    document.body.appendChild(this.overlay);

    // Trigger animation
    requestAnimationFrame(() => {
      this.overlay?.classList.add('modal-overlay--visible');
      this.modal?.classList.add('modal--visible');
    });
  }

  private close(result: boolean): void {
    // Start exit animation
    this.overlay?.classList.remove('modal-overlay--visible');
    this.modal?.classList.remove('modal--visible');

    // Remove from DOM after animation
    setTimeout(() => {
      document.removeEventListener('keydown', this.handleEscKey);
      this.overlay?.remove();
      this.overlay = null;
      this.modal = null;

      // Resolve promise
      if (this.resolveCallback) {
        this.resolveCallback(result);
        this.resolveCallback = null;
      }
    }, 300); // Match CSS transition duration
  }

  /**
   * Static helper for confirm dialogs
   */
  public static async confirm(message: string, title: string = 'Confirm'): Promise<boolean> {
    return new Promise((resolve) => {
      const modal = new Modal({
        title,
        message,
        buttons: [
          {
            text: 'Cancel',
            onClick: () => {
              modal.close(false);
            },
          },
          {
            text: 'Confirm',
            onClick: () => {
              modal.close(true);
            },
            primary: true,
          },
        ],
      });

      // Override close to resolve promise
      const originalResolve = modal.resolveCallback;
      modal.show().then((result) => {
        if (originalResolve) {
          originalResolve(result);
        }
        resolve(result);
      });
    });
  }

  /**
   * Static helper for alert dialogs
   */
  public static async alert(message: string, title: string = 'Alert'): Promise<void> {
    return new Promise((resolve) => {
      const modal = new Modal({
        title,
        message,
        buttons: [
          {
            text: 'OK',
            onClick: () => {
              modal.close(true);
            },
            primary: true,
          },
        ],
      });

      modal.show().then(() => {
        resolve();
      });
    });
  }
}
