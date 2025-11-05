/**
 * Dependency Injection Container
 *
 * Central registry for all services with type-safe resolution.
 * Follows the Dependency Inversion Principle - depend on abstractions, not concretions.
 */

import { ApiService } from './services/api/ApiService.js';
import { GameApiService } from './services/api/GameApiService.js';
import { CatalogApiService } from './services/api/CatalogApiService.js';
import { JournalApiService } from './services/api/JournalApiService.js';
import { StateStore } from './services/state/StateStore.js';
import { SseService } from './services/sse/SseService.js';
import { config } from './config.js';

export interface ServiceContainer {
  apiService: ApiService;
  gameApiService: GameApiService;
  catalogApiService: CatalogApiService;
  journalApiService: JournalApiService;
  stateStore: StateStore;
  sseService: SseService;
}

/**
 * Create and initialize all services
 */
export function createContainer(): ServiceContainer {
  // Create base API service
  const apiService = new ApiService(config.apiBaseUrl);

  // Create specialized API services
  const gameApiService = new GameApiService(apiService);
  const catalogApiService = new CatalogApiService(apiService);
  const journalApiService = new JournalApiService(apiService);

  // Create state management
  const stateStore = new StateStore();

  // Create SSE service
  const sseService = new SseService({
    baseUrl: config.apiBaseUrl,
    reconnectDelay: config.sseReconnectDelay,
    maxReconnectAttempts: config.sseMaxReconnectAttempts,
  });

  return {
    apiService,
    gameApiService,
    catalogApiService,
    journalApiService,
    stateStore,
    sseService,
  };
}

// Global container instance
let containerInstance: ServiceContainer | null = null;

/**
 * Get the global service container instance
 */
export function getContainer(): ServiceContainer {
  if (!containerInstance) {
    containerInstance = createContainer();
  }
  return containerInstance;
}

/**
 * Reset the container (useful for testing)
 */
export function resetContainer(): void {
  if (containerInstance) {
    containerInstance.sseService.disconnect();
    containerInstance.stateStore.reset();
  }
  containerInstance = null;
}
