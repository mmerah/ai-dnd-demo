/**
 * Abstract base Screen class
 *
 * Screens are top-level controllers that manage the overall UI state
 * and coordinate between multiple components.
 */

import { Component } from '../components/base/Component.js';

export abstract class Screen {
  protected container: HTMLElement | null = null;
  protected components: Component<unknown>[] = [];
  private isMounted: boolean = false;

  /**
   * Abstract render method - must be implemented by subclasses
   * Returns the root container for this screen
   */
  protected abstract render(): HTMLElement;

  /**
   * Optional lifecycle hooks - can be overridden by subclasses
   */
  onMount(): void {}
  onUnmount(): void {}

  /**
   * Mount screen to the app container
   */
  mount(parent: HTMLElement): void {
    if (this.isMounted) {
      console.warn('Screen already mounted');
      return;
    }

    this.container = this.render();
    parent.appendChild(this.container);
    this.isMounted = true;
    this.onMount();
  }

  /**
   * Unmount screen and clean up all components
   */
  unmount(): void {
    if (!this.isMounted) {
      return;
    }

    this.onUnmount();

    // Clean up all components
    this.components.forEach(component => component.unmount());
    this.components = [];

    // Remove from DOM
    if (this.container) {
      this.container.remove();
      this.container = null;
    }

    this.isMounted = false;
  }

  /**
   * Register a component for automatic cleanup
   */
  protected registerComponent<TProps>(component: Component<TProps>): void {
    this.components.push(component as Component<unknown>);
  }

  /**
   * Check if screen is currently mounted
   */
  isMountedToDOM(): boolean {
    return this.isMounted;
  }
}
