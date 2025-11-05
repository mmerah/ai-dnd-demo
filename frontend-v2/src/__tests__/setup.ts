/**
 * Global test setup file
 * Runs before all tests
 */

import { vi, afterEach } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();

// Mock EventSource for SSE tests
global.EventSource = vi.fn() as any;

// Reset all mocks after each test
afterEach(() => {
  vi.clearAllMocks();
});
