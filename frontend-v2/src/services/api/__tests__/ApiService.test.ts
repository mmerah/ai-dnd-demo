import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiService } from '../ApiService';
import { ApiError, NetworkError } from '../../../types/errors';

describe('ApiService', () => {
  let apiService: ApiService;
  const baseUrl = 'http://test.api';

  beforeEach(() => {
    apiService = new ApiService(baseUrl);
    vi.clearAllMocks();
  });

  describe('get', () => {
    it('should make GET request with correct URL and headers', async () => {
      const mockResponse = { data: 'test' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.get('/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw ApiError on 4xx response', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: {
          get: () => 'application/json',
        },
        json: async () => ({ detail: 'Resource not found' }),
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(ApiError);
    });

    it('should throw ApiError on 5xx response', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          get: () => null,
        },
        text: async () => 'Server error',
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(ApiError);
    });

    it('should throw NetworkError on network failure', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network failed'));

      await expect(apiService.get('/endpoint')).rejects.toThrow(NetworkError);
      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'Network request failed'
      );
    });

    it('should throw NetworkError on timeout', async () => {
      global.fetch = vi.fn().mockImplementationOnce((_url, options) => {
        return new Promise((_resolve, reject) => {
          // Simulate timeout by listening to abort signal
          if (options?.signal) {
            options.signal.addEventListener('abort', () => {
              const error = new Error('The operation was aborted');
              error.name = 'AbortError';
              reject(error);
            });
          }
        });
      });

      await expect(
        apiService.get('/endpoint', { timeout: 100 })
      ).rejects.toThrow(NetworkError);
    });
  });

  describe('post', () => {
    it('should make POST request with body', async () => {
      const mockResponse = { id: '123' };
      const requestBody = { name: 'Test' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.post('/endpoint', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make POST request without body', async () => {
      const mockResponse = { success: true };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.post('/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle error responses', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          get: () => 'application/json',
        },
        json: async () => ({ error: 'Invalid data' }),
      });

      await expect(apiService.post('/endpoint', {})).rejects.toThrow(ApiError);
    });
  });

  describe('put', () => {
    it('should make PUT request with body', async () => {
      const mockResponse = { updated: true };
      const requestBody = { name: 'Updated' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.put('/endpoint', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestBody),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make PUT request without body', async () => {
      const mockResponse = { updated: true };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.put('/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'PUT',
          body: undefined,
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('delete', () => {
    it('should make DELETE request', async () => {
      const mockResponse = { deleted: true };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.delete('/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle 404 on delete', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: {
          get: () => null,
        },
        text: async () => 'Not found',
      });

      await expect(apiService.delete('/endpoint')).rejects.toThrow(ApiError);
    });
  });

  describe('error body parsing', () => {
    it('should parse JSON error with detail field', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          get: () => 'application/json',
        },
        json: async () => ({ detail: 'Validation error' }),
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'Validation error'
      );
    });

    it('should parse JSON error with message field', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          get: () => 'application/json',
        },
        json: async () => ({ message: 'Error message' }),
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'Error message'
      );
    });

    it('should parse JSON error with error field', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          get: () => 'application/json',
        },
        json: async () => ({ error: 'Error occurred' }),
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'Error occurred'
      );
    });

    it('should parse text error body', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          get: () => 'text/plain',
        },
        text: async () => 'Server error text',
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'Server error text'
      );
    });

    it('should fallback to status text if body parsing fails', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          get: () => 'application/json',
        },
        json: async () => {
          throw new Error('Parse error');
        },
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow(
        'HTTP 500: Internal Server Error'
      );
    });
  });

  describe('timeout handling', () => {
    it('should use default timeout of 30 seconds', async () => {
      const mockResponse = { data: 'test' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await apiService.get('/endpoint');

      // Verify AbortController was used (signal is present)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          signal: expect.any(Object),
        })
      );
    });

    it('should allow custom timeout', async () => {
      const mockResponse = { data: 'test' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await apiService.get('/endpoint', { timeout: 5000 });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          signal: expect.any(Object),
        })
      );
    });
  });

  describe('custom headers', () => {
    it('should merge custom headers with defaults', async () => {
      const mockResponse = { data: 'test' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await apiService.get('/endpoint', {
        headers: {
          'X-Custom-Header': 'custom-value',
        },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
            'X-Custom-Header': 'custom-value',
          },
        })
      );
    });
  });
});
