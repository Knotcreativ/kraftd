/**
 * API Configuration
 *
 * Centralized configuration for API endpoints, timeouts, and constants
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'

export const API_TIMEOUT = 30000 // 30 seconds

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error - please check your connection',
  UNAUTHORIZED: 'Authentication required',
  FORBIDDEN: 'Access denied',
  NOT_FOUND: 'Resource not found',
  QUOTA_EXCEEDED: 'Request limit exceeded - please try again later',
  SERVER_ERROR: 'Server error - please try again later',
  TIMEOUT: 'Request timed out - please try again',
  UNKNOWN_ERROR: 'An unexpected error occurred',
} as const

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'kraftd_jwt',
  REFRESH_TOKEN: 'kraftd_refresh_token',
  USER_DATA: 'kraftd_user',
  THEME: 'kraftd-theme',
} as const