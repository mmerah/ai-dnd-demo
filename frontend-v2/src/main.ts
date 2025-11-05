/**
 * Main application entry point
 *
 * Bootstraps the application by initializing the service container
 * and setting up the UI.
 */

import { getContainer } from './container.js';
import { config } from './config.js';
import { ScreenManager } from './screens/ScreenManager.js';

console.log('AI D&D Frontend v2.0 - TypeScript Edition');
console.log('Configuration:', {
  apiBaseUrl: config.apiBaseUrl,
  isDevelopment: config.isDevelopment,
});

/**
 * Initialize the application
 */
async function initializeApp(): Promise<void> {
  const appContainer = document.getElementById('app');
  if (!appContainer) {
    console.error('App container not found');
    return;
  }

  try {
    // Get service container
    const container = getContainer();

    console.log('Initializing UI...');

    // Initialize screen manager with routing
    const screenManager = new ScreenManager({
      container,
      appContainer,
    });

    // Start routing
    screenManager.initialize();

    console.log('Application initialized successfully!');

    // Try to connect to backend in the background
    tryConnectBackend(container);

  } catch (error) {
    console.error('Failed to initialize application:', error);
    showError(appContainer, error);
  }
}

/**
 * Try to connect to backend (non-blocking)
 */
async function tryConnectBackend(container: ReturnType<typeof getContainer>): Promise<void> {
  try {
    console.log('Testing API connection...');
    const health = await container.gameApiService.checkHealth();
    console.log('API health check:', health);
  } catch (error) {
    console.warn('Backend not available:', error);
    console.log('Running in demo mode - UI will show sample data when state is loaded');
  }
}

/**
 * Show error message to user
 */
function showError(parent: HTMLElement, error: unknown): void {
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = `
    padding: 20px;
    background: #3a1e1e;
    color: #f87171;
    margin: 20px;
    border-radius: 8px;
    border: 1px solid #f87171;
  `;
  errorDiv.innerHTML = `
    <h2>Failed to initialize application</h2>
    <p>An unexpected error occurred during initialization.</p>
    <pre style="margin-top: 10px; padding: 10px; background: #1a1a1a; border-radius: 4px; overflow-x: auto;">${
      error instanceof Error ? error.message : String(error)
    }</pre>
  `;
  parent.appendChild(errorDiv);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
