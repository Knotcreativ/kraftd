/**
 * Base API Client - All API requests go through this
 */

import { API_BASE_URL, API_TIMEOUT, HTTP_STATUS, ERROR_MESSAGES, STORAGE_KEYS } from './config'

export class APIClientError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'APIClientError'
  }
}

interface RequestOptions extends RequestInit {
  timeout?: number
}

/**
 * Core API fetch wrapper
 * - Adds JWT token automatically
 * - Handles errors centrally
 * - Manages timeouts
 * - Provides typed responses
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeout = API_TIMEOUT, ...fetchOptions } = options

  // Build headers
  const headers = new Headers(fetchOptions.headers)
  headers.set('Content-Type', 'application/json')

  // Add JWT token if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  // Build URL
  const url = `${API_BASE_URL}${path}`

  // Create abort controller for timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    // Handle non-OK responses
    if (!response.ok) {
      await handleErrorResponse(response)
    }

    // Parse response
    const data = await response.json()
    return data as T
  } catch (error) {
    clearTimeout(timeoutId)

    // Handle abort (timeout)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new APIClientError(
        HTTP_STATUS.INTERNAL_SERVER_ERROR,
        ERROR_MESSAGES.TIMEOUT
      )
    }

    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIClientError(
        HTTP_STATUS.INTERNAL_SERVER_ERROR,
        ERROR_MESSAGES.NETWORK_ERROR
      )
    }

    throw error
  }
}

/**
 * Handle error responses with specific status codes
 */
async function handleErrorResponse(response: Response): Promise<never> {
  const status = response.status
  let data: Record<string, unknown> | undefined

  // Try to parse error body
  try {
    data = await response.json() as Record<string, unknown>
  } catch {
    // If response isn't JSON, that's okay
  }

  // Get appropriate error message
  let message: string = ERROR_MESSAGES.SERVER_ERROR
  if (data && typeof data.message === 'string') {
    message = data.message
  }

  switch (status) {
    case HTTP_STATUS.UNAUTHORIZED:
      message = ERROR_MESSAGES.UNAUTHORIZED
      // Clear token and redirect handled by auth context
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      }
      break
    case HTTP_STATUS.FORBIDDEN:
      message = ERROR_MESSAGES.FORBIDDEN
      break
    case HTTP_STATUS.NOT_FOUND:
      message = ERROR_MESSAGES.NOT_FOUND
      break
    case HTTP_STATUS.TOO_MANY_REQUESTS:
      message = ERROR_MESSAGES.QUOTA_EXCEEDED
      break
  }

  throw new APIClientError(status, message, data)
}

/**
 * Convenience method for GET requests
 */
export function apiGet<T = unknown>(path: string, options?: RequestOptions) {
  return apiFetch<T>(path, { ...options, method: 'GET' })
}

/**
 * Convenience method for POST requests
 */
export function apiPost<T = unknown>(
  path: string,
  body?: Record<string, unknown>,
  options?: RequestOptions
) {
  return apiFetch<T>(path, {
    ...options,
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * Convenience method for PUT requests
 */
export function apiPut<T = unknown>(
  path: string,
  body?: Record<string, unknown>,
  options?: RequestOptions
) {
  return apiFetch<T>(path, {
    ...options,
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * Convenience method for DELETE requests
 */
export function apiDelete<T = unknown>(path: string, options?: RequestOptions) {
  return apiFetch<T>(path, { ...options, method: 'DELETE' })
}
