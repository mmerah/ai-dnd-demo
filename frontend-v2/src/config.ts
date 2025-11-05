/**
 * Application configuration
 */

export const config = {
    apiBaseUrl: import.meta.env.VITE_API_URL || '/api',
    sseReconnectDelay: 3000,
    sseMaxRetries: 5,
} as const;
