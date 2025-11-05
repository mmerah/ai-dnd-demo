/**
 * Observable pattern implementation for reactive state management
 *
 * Provides a simple pub/sub mechanism for state changes with type safety.
 * Listeners are notified immediately when the value changes.
 */

export type Listener<T> = (value: T) => void;
export type Unsubscribe = () => void;

export class Observable<T> {
  private listeners: Set<Listener<T>> = new Set();
  private value: T;

  constructor(initialValue: T) {
    this.value = initialValue;
  }

  /**
   * Get the current value
   */
  get(): T {
    return this.value;
  }

  /**
   * Set a new value and notify all listeners
   * Only notifies if the value has actually changed (referential equality check)
   */
  set(newValue: T): void {
    if (this.value !== newValue) {
      this.value = newValue;
      this.notify();
    }
  }

  /**
   * Subscribe to value changes
   * Returns an unsubscribe function
   */
  subscribe(listener: Listener<T>): Unsubscribe {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Subscribe and immediately call the listener with the current value
   */
  subscribeImmediate(listener: Listener<T>): Unsubscribe {
    const unsubscribe = this.subscribe(listener);
    listener(this.value);
    return unsubscribe;
  }

  /**
   * Notify all listeners of the current value
   */
  private notify(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.value);
      } catch (error) {
        // Log error but don't stop other listeners from being notified
        console.error('Error in Observable listener:', error);
      }
    });
  }

  /**
   * Get the number of active listeners (useful for debugging)
   */
  get listenerCount(): number {
    return this.listeners.size;
  }

  /**
   * Clear all listeners (useful for cleanup)
   */
  clearListeners(): void {
    this.listeners.clear();
  }
}
