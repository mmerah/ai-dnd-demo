/**
 * Custom error classes for type-safe error handling
 */

export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly cause?: unknown
  ) {
    super(message);
    this.name = this.constructor.name;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

export class ApiError extends AppError {
  constructor(
    public readonly status: number,
    message: string,
    cause?: unknown
  ) {
    super(message, 'API_ERROR', cause);
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

export class NetworkError extends AppError {
  constructor(message: string, cause?: unknown) {
    super(message, 'NETWORK_ERROR', cause);
  }
}

export class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly field?: string,
    cause?: unknown
  ) {
    super(message, 'VALIDATION_ERROR', cause);
  }
}

export class StateError extends AppError {
  constructor(message: string, cause?: unknown) {
    super(message, 'STATE_ERROR', cause);
  }
}

export class SseError extends AppError {
  constructor(message: string, cause?: unknown) {
    super(message, 'SSE_ERROR', cause);
  }
}

/**
 * Type guard to check if an error is an AppError
 */
export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}

/**
 * Type guard to check if an error is an ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/**
 * Type guard to check if an error is a NetworkError
 */
export function isNetworkError(error: unknown): error is NetworkError {
  return error instanceof NetworkError;
}

/**
 * Safely extract error message from unknown error
 */
export function getErrorMessage(error: unknown): string {
  if (isAppError(error)) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return 'An unknown error occurred';
}
