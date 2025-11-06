import { describe, it, expect, vi } from 'vitest';
import { Observable } from '../Observable';

describe('Observable', () => {
  describe('constructor and get', () => {
    it('should initialize with given value', () => {
      const observable = new Observable<number>(42);
      expect(observable.get()).toBe(42);
    });

    it('should initialize with null', () => {
      const observable = new Observable<string | null>(null);
      expect(observable.get()).toBeNull();
    });

    it('should initialize with object', () => {
      const obj = { key: 'value' };
      const observable = new Observable(obj);
      expect(observable.get()).toBe(obj);
    });
  });

  describe('set', () => {
    it('should update value', () => {
      const observable = new Observable<number>(10);
      observable.set(20);
      expect(observable.get()).toBe(20);
    });

    it('should notify listeners on value change', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();
      observable.subscribe(listener);

      observable.set(20);

      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener).toHaveBeenCalledWith(20);
    });

    it('should not notify listeners if value is the same (referential equality)', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();
      observable.subscribe(listener);

      observable.set(10);

      expect(listener).not.toHaveBeenCalled();
    });

    it('should notify multiple listeners', () => {
      const observable = new Observable<number>(10);
      const listener1 = vi.fn();
      const listener2 = vi.fn();
      const listener3 = vi.fn();

      observable.subscribe(listener1);
      observable.subscribe(listener2);
      observable.subscribe(listener3);

      observable.set(20);

      expect(listener1).toHaveBeenCalledWith(20);
      expect(listener2).toHaveBeenCalledWith(20);
      expect(listener3).toHaveBeenCalledWith(20);
    });

    it('should handle object reference changes', () => {
      const obj1 = { value: 1 };
      const obj2 = { value: 1 };
      const observable = new Observable(obj1);
      const listener = vi.fn();
      observable.subscribe(listener);

      observable.set(obj2);

      // Different references, so should notify
      expect(listener).toHaveBeenCalledWith(obj2);
    });
  });

  describe('subscribe', () => {
    it('should add listener', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      observable.subscribe(listener);

      expect(observable.listenerCount).toBe(1);
    });

    it('should return unsubscribe function', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      const unsubscribe = observable.subscribe(listener);

      expect(typeof unsubscribe).toBe('function');
      expect(observable.listenerCount).toBe(1);

      unsubscribe();

      expect(observable.listenerCount).toBe(0);
    });

    it('should not call listener immediately on subscribe', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      observable.subscribe(listener);

      expect(listener).not.toHaveBeenCalled();
    });

    it('should allow multiple subscriptions', () => {
      const observable = new Observable<number>(10);
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      observable.subscribe(listener1);
      observable.subscribe(listener2);

      expect(observable.listenerCount).toBe(2);
    });

    it('should not notify unsubscribed listeners', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      const unsubscribe = observable.subscribe(listener);
      unsubscribe();

      observable.set(20);

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('subscribeImmediate', () => {
    it('should call listener immediately with current value', () => {
      const observable = new Observable<number>(42);
      const listener = vi.fn();

      observable.subscribeImmediate(listener);

      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener).toHaveBeenCalledWith(42);
    });

    it('should also notify on future value changes', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      observable.subscribeImmediate(listener);
      observable.set(20);

      expect(listener).toHaveBeenCalledTimes(2);
      expect(listener).toHaveBeenNthCalledWith(1, 10);
      expect(listener).toHaveBeenNthCalledWith(2, 20);
    });

    it('should return working unsubscribe function', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      const unsubscribe = observable.subscribeImmediate(listener);
      listener.mockClear(); // Clear the immediate call

      unsubscribe();
      observable.set(20);

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should not stop other listeners if one throws', () => {
      const observable = new Observable<number>(10);
      const errorListener = vi.fn(() => {
        throw new Error('Listener error');
      });
      const goodListener = vi.fn();

      observable.subscribe(errorListener);
      observable.subscribe(goodListener);

      // Mock console.error to avoid test output pollution
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      observable.set(20);

      expect(errorListener).toHaveBeenCalledWith(20);
      expect(goodListener).toHaveBeenCalledWith(20);
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('listenerCount', () => {
    it('should return 0 initially', () => {
      const observable = new Observable<number>(10);
      expect(observable.listenerCount).toBe(0);
    });

    it('should track number of listeners', () => {
      const observable = new Observable<number>(10);

      const unsub1 = observable.subscribe(() => {});
      expect(observable.listenerCount).toBe(1);

      const unsub2 = observable.subscribe(() => {});
      expect(observable.listenerCount).toBe(2);

      unsub1();
      expect(observable.listenerCount).toBe(1);

      unsub2();
      expect(observable.listenerCount).toBe(0);
    });
  });

  describe('clearListeners', () => {
    it('should remove all listeners', () => {
      const observable = new Observable<number>(10);
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      observable.subscribe(listener1);
      observable.subscribe(listener2);

      expect(observable.listenerCount).toBe(2);

      observable.clearListeners();

      expect(observable.listenerCount).toBe(0);

      observable.set(20);
      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).not.toHaveBeenCalled();
    });

    it('should handle being called with no listeners', () => {
      const observable = new Observable<number>(10);
      expect(() => observable.clearListeners()).not.toThrow();
    });
  });

  describe('type safety', () => {
    it('should work with string type', () => {
      const observable = new Observable<string>('hello');
      const listener = vi.fn();

      observable.subscribe(listener);
      observable.set('world');

      expect(listener).toHaveBeenCalledWith('world');
    });

    it('should work with complex object type', () => {
      interface User {
        name: string;
        age: number;
      }

      const user: User = { name: 'Alice', age: 30 };
      const observable = new Observable<User>(user);
      const listener = vi.fn();

      observable.subscribe(listener);

      const updatedUser: User = { name: 'Bob', age: 25 };
      observable.set(updatedUser);

      expect(listener).toHaveBeenCalledWith(updatedUser);
    });

    it('should work with union types', () => {
      const observable = new Observable<string | null>(null);
      const listener = vi.fn();

      observable.subscribe(listener);
      observable.set('value');

      expect(listener).toHaveBeenCalledWith('value');
    });
  });

  describe('cleanup patterns', () => {
    it('should properly clean up multiple subscribers', () => {
      const observable = new Observable<number>(10);
      const unsubscribers = [];

      for (let i = 0; i < 5; i++) {
        unsubscribers.push(observable.subscribe(() => {}));
      }

      expect(observable.listenerCount).toBe(5);

      unsubscribers.forEach(unsub => unsub());

      expect(observable.listenerCount).toBe(0);
    });

    it('should handle unsubscribe being called multiple times', () => {
      const observable = new Observable<number>(10);
      const listener = vi.fn();

      const unsubscribe = observable.subscribe(listener);

      expect(observable.listenerCount).toBe(1);

      unsubscribe();
      unsubscribe();
      unsubscribe();

      expect(observable.listenerCount).toBe(0);
    });
  });
});
