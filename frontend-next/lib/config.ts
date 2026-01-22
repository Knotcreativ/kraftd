/**
 * API Client Configuration
 */

export const API_BASE_URL =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
    : process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'

export const API_TIMEOUT = 30000 // 30 seconds

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
} as const

// Error Messages
export const ERROR_MESSAGES = {
  UNAUTHORIZED: 'Please log in to continue',
  FORBIDDEN: 'You do not have access to this resource',
  NOT_FOUND: 'Resource not found',
  QUOTA_EXCEEDED: 'You have reached your plan limit',
  SERVER_ERROR: 'An unexpected error occurred. Please try again later.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timed out. Please try again.',
} as const

// Local Storage Keys
export const STORAGE_KEYS = {
  JWT_TOKEN: 'kraftd_jwt_token',
  REFRESH_TOKEN: 'kraftd_refresh_token',
  USER: 'kraftd_user',
  USER_EMAIL: 'kraftd_user_email',
  PREFERENCES: 'kraftd_preferences',
} as const
