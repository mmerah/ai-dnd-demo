/**
 * Abstract base component class with lifecycle management
 *
 * Provides a consistent pattern for building UI components with:
 * - Lifecycle hooks (onMount, onUpdate, onUnmount)
 * - Automatic subscription cleanup
 * - Type-safe props
 * - Virtual DOM-like update pattern
 */

import { Observable, Unsubscribe } from '../../services/state/Observable.js';

export interface ComponentLifecycle {
  /**
   * Called after component is mounted to DOM
   */
  onMount?(): void;

  /**
   * Called when props change and component is re-rendered
   */
  onUpdate?(prevProps: unknown): void;

  /**
   * Called before component is removed from DOM
   */
  onUnmount?(): void;
}

export abstract class Component<TProps = Record<string, never>> implements ComponentLifecycle {
  protected element: HTMLElement | null = null;
  protected props: TProps;
  private subscriptions: Unsubscribe[] = [];
  private isMounted: boolean = false;

  constructor(props: TProps) {
    this.props = props;
  }

  /**
   * Abstract render method - must be implemented by subclasses
   * Returns the root element for this component
   */
  protected abstract render(): HTMLElement;

  /**
   * Optional lifecycle hooks - can be overridden by subclasses
   */
  onMount(): void {}
  onUpdate(_prevProps: TProps): void {}
  onUnmount(): void {}

  /**
   * Mount component to a parent element
   */
  mount(parent: HTMLElement): void {
    if (this.isMounted) {
      console.warn('Component already mounted');
      return;
    }

    this.element = this.render();
    parent.appendChild(this.element);
    this.isMounted = true;
    this.onMount();
  }

  /**
   * Update component with new props
   * Triggers re-render and onUpdate lifecycle hook
   */
  update(newProps: Partial<TProps>): void {
    if (!this.isMounted || !this.element) {
      console.warn('Cannot update unmounted component');
      return;
    }

    const prevProps = { ...this.props };
    this.props = { ...this.props, ...newProps };

    // Re-render
    const newElement = this.render();
    this.element.replaceWith(newElement);
    this.element = newElement;

    this.onUpdate(prevProps);
  }

  /**
   * Unmount component and clean up resources
   */
  unmount(): void {
    if (!this.isMounted) {
      return;
    }

    this.onUnmount();

    // Clean up all subscriptions
    this.subscriptions.forEach(unsubscribe => unsubscribe());
    this.subscriptions = [];

    // Remove from DOM
    if (this.element) {
      this.element.remove();
      this.element = null;
    }

    this.isMounted = false;
  }

  /**
   * Subscribe to an Observable with automatic cleanup
   * Subscription will be automatically cleaned up when component unmounts
   */
  protected subscribe<T>(
    observable: Observable<T>,
    callback: (value: T) => void
  ): void {
    const unsubscribe = observable.subscribe(callback);
    this.subscriptions.push(unsubscribe);
  }

  /**
   * Subscribe to an Observable and immediately invoke callback
   */
  protected subscribeImmediate<T>(
    observable: Observable<T>,
    callback: (value: T) => void
  ): void {
    const unsubscribe = observable.subscribeImmediate(callback);
    this.subscriptions.push(unsubscribe);
  }

  /**
   * Check if component is currently mounted
   */
  isMountedToDOM(): boolean {
    return this.isMounted;
  }

  /**
   * Get the root element (null if not mounted)
   */
  getElement(): HTMLElement | null {
    return this.element;
  }
}
