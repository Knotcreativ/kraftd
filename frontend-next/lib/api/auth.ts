/**
 * Authentication API Client
 *
 * Provides all authentication-related API calls:
 * - Login with email/password
 * - Register new user
 * - Refresh access token
 * - Get user profile
 * - Logout
 */

import { apiPost, apiGet } from './client'
import { API_BASE_URL } from './config'
import type { User } from '../types'

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface RegisterResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface RefreshResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * Login with email and password
 *
 * @param email User email address
 * @param password User password
 * @returns Access and refresh tokens
 */
export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  const response = await apiPost<LoginResponse>('/auth/login', {
    email,
    password,
  })
  return response
}

/**
 * Register new user
 *
 * @param email User email address
 * @param password User password
 * @param firstName User's first name
 * @param lastName User's last name
 * @param acceptTerms Accept terms of service
 * @param acceptPrivacy Accept privacy policy
 * @returns Access and refresh tokens
 */
export async function register(
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  acceptTerms: boolean,
  acceptPrivacy: boolean
): Promise<RegisterResponse> {
  const response = await apiPost<RegisterResponse>('/auth/register', {
    email,
    password,
    firstName,
    lastName,
    acceptTerms,
    acceptPrivacy,
  })
  return response
}

/**
 * Refresh access token using refresh token
 *
 * @param refreshToken The refresh token
 * @returns New access token
 */
export async function refresh(
  refreshToken: string
): Promise<RefreshResponse> {
  // Use raw fetch to avoid Authorization header auto-injection
  // since we haven't gotten a new access token yet
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Token refresh failed')
  }

  const data = await response.json()
  return data as RefreshResponse
}

/**
 * Get current user profile
 *
 * @param accessToken The access token (optional, uses stored token if not provided)
 * @returns User profile
 */
export async function getProfile(accessToken?: string): Promise<User> {
  // If access token provided, temporarily use it
  if (accessToken) {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to fetch profile')
    }

    return response.json() as Promise<User>
  }

  // Otherwise use normal API call with stored token
  return apiGet<User>('/auth/me')
}

/**
 * Logout (optional backend call)
 *
 * @param accessToken The access token to invalidate
 */
export async function logout(accessToken: string): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
    })
  } catch (error) {
    // Logout can fail silently - client will still clear auth state
    console.error('Logout failed:', error)
  }
}

/**
 * Storage key management (legacy compatibility)
 */

export function storeToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('kraftd_jwt', token)
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('kraftd_jwt')
  }
  return null
}

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('kraftd_jwt')
  }
}
