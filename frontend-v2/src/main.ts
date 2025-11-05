/**
 * Main application entry point
 *
 * Bootstraps the application by initializing the service container
 * and setting up the UI.
 */

import { getContainer } from './container.js';
import { config } from './config.js';

console.log('AI D&D Frontend v2.0 - TypeScript Edition');
console.log('Configuration:', {
  apiBaseUrl: config.apiBaseUrl,
  isDevelopment: config.isDevelopment,
});

/**
 * Initialize the application
 */
async function initializeApp(): Promise<void> {
  try {
    // Get service container
    const container = getContainer();

    // Test API connection
    console.log('Testing API connection...');
    const health = await container.gameApiService.checkHealth();
    console.log('API health check:', health);

    // Initialize UI
    console.log('Initializing UI...');
    // TODO: Initialize screen controllers and mount UI components

    console.log('Application initialized successfully!');
  } catch (error) {
    console.error('Failed to initialize application:', error);

    // Show error to user
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'padding: 20px; background: #fee; color: #c00; margin: 20px; border-radius: 4px;';
    errorDiv.innerHTML = `
      <h2>Failed to initialize application</h2>
      <p>Could not connect to the backend server.</p>
      <p>Please ensure the backend is running at <code>${config.apiBaseUrl}</code></p>
      <pre>${error instanceof Error ? error.message : String(error)}</pre>
    `;
    document.body.appendChild(errorDiv);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
