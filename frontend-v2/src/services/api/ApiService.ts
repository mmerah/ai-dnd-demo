/**
 * Base API service with error handling and type safety
 *
 * Provides a consistent interface for making HTTP requests with proper
 * error handling, timeout management, and response validation.
 */

import { ApiError, NetworkError } from '../../types/errors.js';

export interface RequestConfig extends RequestInit {
  timeout?: number;
}

/**
 * Base API service for making HTTP requests
 */
export class ApiService {
  private readonly baseUrl: string;
  private readonly defaultTimeout: number = 30000; // 30 seconds

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make an HTTP request with error handling
   */
  async request<TResponse>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<TResponse> {
    const { timeout = this.defaultTimeout, ...fetchOptions } = config;
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorBody = await this.parseErrorBody(response);
        throw new ApiError(
          response.status,
          errorBody || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      // Re-throw our custom errors
      if (error instanceof ApiError) {
        throw error;
      }

      // Handle abort errors (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout', error);
      }

      // Handle network errors
      throw new NetworkError('Network request failed', error);
    }
  }

  /**
   * GET request
   */
  async get<TResponse>(
    endpoint: string,
    config?: RequestConfig
  ): Promise<TResponse> {
    return this.request<TResponse>(endpoint, {
      ...config,
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post<TResponse, TBody = unknown>(
    endpoint: string,
    body?: TBody,
    config?: RequestConfig
  ): Promise<TResponse> {
    return this.request<TResponse>(endpoint, {
      ...config,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<TResponse, TBody = unknown>(
    endpoint: string,
    body?: TBody,
    config?: RequestConfig
  ): Promise<TResponse> {
    return this.request<TResponse>(endpoint, {
      ...config,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PATCH request
   */
  async patch<TResponse, TBody = unknown>(
    endpoint: string,
    body?: TBody,
    config?: RequestConfig
  ): Promise<TResponse> {
    return this.request<TResponse>(endpoint, {
      ...config,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<TResponse>(
    endpoint: string,
    config?: RequestConfig
  ): Promise<TResponse> {
    return this.request<TResponse>(endpoint, {
      ...config,
      method: 'DELETE',
    });
  }

  /**
   * Parse error response body
   */
  private async parseErrorBody(response: Response): Promise<string | null> {
    try {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const json = await response.json();
        return json.detail || json.message || json.error || null;
      }
      return await response.text();
    } catch {
      return null;
    }
  }
}
