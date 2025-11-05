/**
 * Application configuration
 *
 * Centralized configuration with environment variable support.
 * All configuration should be defined here for easy management.
 */

export interface AppConfig {
  apiBaseUrl: string;
  sseReconnectDelay: number;
  sseMaxReconnectAttempts: number;
  isDevelopment: boolean;
}

/**
 * Get configuration from environment or use defaults
 */
function loadConfig(): AppConfig {
  // Check if we're in development mode
  const isDevelopment = import.meta.env?.DEV ?? false;

  // API base URL - use proxy in dev, direct in production
  const apiBaseUrl = import.meta.env?.VITE_API_BASE_URL ??
    (isDevelopment ? 'http://localhost:8123' : '');

  return {
    apiBaseUrl,
    sseReconnectDelay: 3000, // 3 seconds
    sseMaxReconnectAttempts: 5,
    isDevelopment,
  };
}

export const config: AppConfig = loadConfig();
