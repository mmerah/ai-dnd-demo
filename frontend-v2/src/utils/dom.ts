/**
 * DOM utility functions
 *
 * Pure helper functions for DOM manipulation and creation.
 * All functions are side-effect free except for DOM mutation.
 */

export type DOMAttributes = Record<string, string | number | boolean | ((event: Event) => void)>;

/**
 * Create an HTML element with attributes and children
 */
export function createElement(
  tag: string,
  attributes?: DOMAttributes,
  ...children: (string | HTMLElement | null | undefined)[]
): HTMLElement {
  const element = document.createElement(tag);

  // Set attributes
  if (attributes) {
    Object.entries(attributes).forEach(([key, value]) => {
      if (key.startsWith('on') && typeof value === 'function') {
        // Event listener
        const eventName = key.substring(2).toLowerCase();
        element.addEventListener(eventName, value as EventListener);
      } else if (key === 'className' || key === 'class') {
        // Class name
        element.className = String(value);
      } else if (key === 'style' && typeof value === 'object') {
        // Inline styles object
        Object.assign(element.style, value);
      } else {
        // Regular attribute
        element.setAttribute(key, String(value));
      }
    });
  }

  // Append children
  children.forEach(child => {
    if (child === null || child === undefined) {
      return;
    }

    if (typeof child === 'string') {
      element.appendChild(document.createTextNode(child));
    } else {
      element.appendChild(child);
    }
  });

  return element;
}

/**
 * Create a div element (convenience function)
 */
export function div(
  attributes?: DOMAttributes,
  ...children: (string | HTMLElement | null | undefined)[]
): HTMLElement {
  return createElement('div', attributes, ...children);
}

/**
 * Create a span element (convenience function)
 */
export function span(
  attributes?: DOMAttributes,
  ...children: (string | HTMLElement | null | undefined)[]
): HTMLElement {
  return createElement('span', attributes, ...children);
}

/**
 * Create a button element (convenience function)
 */
export function button(
  text: string,
  attributes?: DOMAttributes
): HTMLElement {
  return createElement('button', attributes, text);
}

/**
 * Create an input element (convenience function)
 */
export function input(attributes?: DOMAttributes): HTMLInputElement {
  return createElement('input', attributes) as HTMLInputElement;
}

/**
 * Safely escape HTML to prevent XSS
 */
export function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Set innerHTML safely by escaping HTML
 */
export function setTextContent(element: HTMLElement, text: string): void {
  element.textContent = text;
}

/**
 * Remove all children from an element
 */
export function clearElement(element: HTMLElement): void {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

/**
 * Add CSS classes to an element
 */
export function addClass(element: HTMLElement, ...classes: string[]): void {
  element.classList.add(...classes);
}

/**
 * Remove CSS classes from an element
 */
export function removeClass(element: HTMLElement, ...classes: string[]): void {
  element.classList.remove(...classes);
}

/**
 * Toggle CSS class on an element
 */
export function toggleClass(element: HTMLElement, className: string, force?: boolean): void {
  element.classList.toggle(className, force);
}

/**
 * Check if element has a CSS class
 */
export function hasClass(element: HTMLElement, className: string): boolean {
  return element.classList.contains(className);
}

/**
 * Query selector helper with type safety
 */
export function query<T extends HTMLElement = HTMLElement>(
  selector: string,
  parent: HTMLElement | Document = document
): T | null {
  return parent.querySelector<T>(selector);
}

/**
 * Query selector all helper with type safety
 */
export function queryAll<T extends HTMLElement = HTMLElement>(
  selector: string,
  parent: HTMLElement | Document = document
): T[] {
  return Array.from(parent.querySelectorAll<T>(selector));
}
