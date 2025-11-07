/**
 * Toast Notification System
 *
 * Provides simple, non-blocking user feedback for success, error, and info messages.
 * Toasts auto-dismiss after 3 seconds and are stacked vertically.
 *
 * Usage:
 * Toast.show('Item equipped successfully', 'success');
 * Toast.show('Failed to equip item', 'error');
 * Toast.show('Game auto-saves on every action', 'info');
 */

import { div } from '../../utils/dom.js';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastOptions {
  /**
   * Toast type determines icon and color
   */
  type: ToastType;

  /**
   * Message to display
   */
  message: string;

  /**
   * Duration in milliseconds before auto-dismiss
   * @default 3000
   */
  duration?: number;
}

/**
 * Toast notification manager
 * Singleton pattern for managing toast lifecycle
 */
export class Toast {
  private static container: HTMLElement | null = null;
  private static activeToasts: Set<HTMLElement> = new Set();

  /**
   * Show a toast notification
   */
  public static show(message: string, type: ToastType = 'info', duration: number = 3000): void {
    // Ensure container exists
    this.ensureContainer();

    // Create toast element
    const toast = this.createToast(message, type);

    // Add to container
    this.container?.appendChild(toast);
    this.activeToasts.add(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('toast--visible');
    });

    // Auto-dismiss after duration
    setTimeout(() => {
      this.dismiss(toast);
    }, duration);
  }

  /**
   * Convenience methods for common toast types
   */
  public static success(message: string, duration?: number): void {
    this.show(message, 'success', duration);
  }

  public static error(message: string, duration?: number): void {
    this.show(message, 'error', duration);
  }

  public static info(message: string, duration?: number): void {
    this.show(message, 'info', duration);
  }

  public static warning(message: string, duration?: number): void {
    this.show(message, 'warning', duration);
  }

  /**
   * Dismiss a toast
   */
  private static dismiss(toast: HTMLElement): void {
    // Start exit animation
    toast.classList.remove('toast--visible');
    toast.classList.add('toast--exiting');

    // Remove from DOM after animation
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
      this.activeToasts.delete(toast);

      // Clean up container if no more toasts
      if (this.activeToasts.size === 0 && this.container) {
        this.container.remove();
        this.container = null;
      }
    }, 300); // Match CSS transition duration
  }

  /**
   * Create toast element with proper styling
   */
  private static createToast(message: string, type: ToastType): HTMLElement {
    const toast = div({ class: `toast toast--${type}` });

    // Icon based on type
    const icon = this.getIcon(type);
    const iconEl = div({ class: 'toast__icon' });
    iconEl.textContent = icon;

    // Message
    const messageEl = div({ class: 'toast__message' });
    messageEl.textContent = message;

    // Close button
    const closeBtn = div({ class: 'toast__close' });
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => this.dismiss(toast));

    toast.appendChild(iconEl);
    toast.appendChild(messageEl);
    toast.appendChild(closeBtn);

    return toast;
  }

  /**
   * Get icon for toast type
   */
  private static getIcon(type: ToastType): string {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return 'ℹ';
    }
  }

  /**
   * Ensure toast container exists in DOM
   */
  private static ensureContainer(): void {
    if (!this.container) {
      this.container = div({ class: 'toast-container' });
      document.body.appendChild(this.container);
    }
  }

  /**
   * Clear all active toasts (useful for cleanup/testing)
   */
  public static clearAll(): void {
    this.activeToasts.forEach(toast => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
    });
    this.activeToasts.clear();

    if (this.container) {
      this.container.remove();
      this.container = null;
    }
  }
}
