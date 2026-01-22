/**
 * useAuth Hook - Complete authentication state management
 *
 * Features:
 * - Email/password login and registration
 * - JWT token management (access + refresh)
 * - Auto-token refresh when expired
 * - Token persistence (localStorage)
 * - User profile caching
 * - Error handling with user-friendly messages
 * - Loading states for all operations
 */

'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import * as authAPI from '@/lib/api/auth'
import { STORAGE_KEYS } from '@/lib/config'
import type { User } from '@/lib/types'

interface LoginCredentials {
  email: string
  password: string
}

interface RegisterCredentials {
  email: string
  password: string
  firstName: string
  lastName: string
  acceptTerms: boolean
  acceptPrivacy: boolean
}

export function useAuth() {
  const router = useRouter()
  
  // State
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Refs for token refresh timing
  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const refreshRef = useRef<(() => Promise<{ success: boolean; error?: string }>) | null>(null)

  // Clear all auth state
  const clearAuthState = useCallback(() => {
    setUser(null)
    setAccessToken(null)
    setRefreshToken(null)
    localStorage.removeItem(STORAGE_KEYS.JWT_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current)
    }
  }, [])

  // Schedule token refresh before expiration
  const scheduleTokenRefresh = useCallback((token: string) => {
    try {
      // Decode token to get expiration
      const parts = token.split('.')
      if (parts.length !== 3) return

      const payload = JSON.parse(
        Buffer.from(parts[1], 'base64').toString('utf-8')
      )
      const expiration = payload.exp * 1000 // Convert to milliseconds
      const now = Date.now()
      const timeUntilExpire = expiration - now

      // Refresh 5 minutes before expiration
      const refreshTime = timeUntilExpire - 5 * 60 * 1000

      if (refreshTime > 0) {
        if (refreshTimeoutRef.current) {
          clearTimeout(refreshTimeoutRef.current)
        }

        refreshTimeoutRef.current = setTimeout(() => {
          // Call refresh function via ref
          if (refreshRef.current) {
            refreshRef.current()
          }
        }, refreshTime)
      }
    } catch (err) {
      console.error('Error scheduling token refresh:', err)
    }
  }, [])

  // Refresh access token
  const refresh = useCallback(async () => {
    if (!refreshToken) return { success: false, error: 'No refresh token' }

    try {
      const response = await authAPI.refresh(refreshToken)

      // Update access token
      localStorage.setItem(STORAGE_KEYS.JWT_TOKEN, response.access_token)
      setAccessToken(response.access_token)

      // Schedule next refresh
      scheduleTokenRefresh(response.access_token)

      return { success: true }
    } catch (err) {
      // Refresh failed, clear auth state and redirect to login
      clearAuthState()
      router.push('/login')
      const message =
        err instanceof Error ? err.message : 'Session expired. Please log in again.'
      setError(message)
      return { success: false, error: message }
    }
  }, [refreshToken, scheduleTokenRefresh, clearAuthState, router])

  // Update the ref
  useEffect(() => {
    refreshRef.current = refresh
  }, [refresh])

  // Initialize auth state from localStorage and verify token
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true)
      try {
        // Get tokens from localStorage
        const storedAccessToken = localStorage.getItem(STORAGE_KEYS.JWT_TOKEN)
        const storedRefreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)

        if (storedAccessToken) {
          setAccessToken(storedAccessToken)
          setRefreshToken(storedRefreshToken)

          // Verify token is still valid
          try {
            const profile = await authAPI.getProfile(storedAccessToken)
            setUser(profile)
            // Schedule token refresh
            scheduleTokenRefresh(storedAccessToken)
          } catch {
            // Token invalid, clear storage
            clearAuthState()
          }
        }
      } catch (err) {
        console.error('Error initializing auth:', err)
        clearAuthState()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()

    // Cleanup timeout on unmount
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current)
      }
    }
  }, [clearAuthState, scheduleTokenRefresh])

  // Login with email and password
  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsAuthenticating(true)
      setError(null)

      try {
        // Call login API
        const response = await authAPI.login(
          credentials.email,
          credentials.password
        )

        // Store tokens
        localStorage.setItem(STORAGE_KEYS.JWT_TOKEN, response.access_token)
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token)

        setAccessToken(response.access_token)
        setRefreshToken(response.refresh_token)

        // Get user profile
        try {
          const profile = await authAPI.getProfile(response.access_token)
          setUser(profile)
          localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(profile))
        } catch (err) {
          console.error('Error fetching profile after login:', err)
        }

        // Schedule token refresh
        scheduleTokenRefresh(response.access_token)

        // Redirect to dashboard
        router.push('/')

        return { success: true }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Login failed. Please try again.'
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsAuthenticating(false)
      }
    },
    [router, scheduleTokenRefresh]
  )

  // Register new user
  const register = useCallback(
    async (credentials: RegisterCredentials) => {
      setIsAuthenticating(true)
      setError(null)

      try {
        // Call register API
        const response = await authAPI.register(
          credentials.email,
          credentials.password,
          credentials.firstName,
          credentials.lastName,
          credentials.acceptTerms,
          credentials.acceptPrivacy
        )

        // Store tokens
        localStorage.setItem(STORAGE_KEYS.JWT_TOKEN, response.access_token)
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token)

        setAccessToken(response.access_token)
        setRefreshToken(response.refresh_token)

        // Get user profile
        try {
          const profile = await authAPI.getProfile(response.access_token)
          setUser(profile)
          localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(profile))
        } catch (err) {
          console.error('Error fetching profile after registration:', err)
        }

        // Schedule token refresh
        scheduleTokenRefresh(response.access_token)

        // Redirect to dashboard
        router.push('/')

        return { success: true }
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'Registration failed. Please try again.'
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsAuthenticating(false)
      }
    },
    [router, scheduleTokenRefresh]
  )

  // Logout
  const logout = useCallback(async () => {
    try {
      // Attempt to invalidate token on backend (optional)
      if (accessToken) {
        try {
          await authAPI.logout(accessToken)
        } catch (err) {
          // Logout can still proceed even if backend call fails
          console.error('Error calling logout endpoint:', err)
        }
      }
    } finally {
      // Always clear local auth state
      clearAuthState()
      router.push('/login')
    }
  }, [accessToken, clearAuthState, router])

  // Check if authenticated
  const isAuthenticated = !!accessToken && !!user

  return {
    // State
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading,
    isAuthenticating,
    error,

    // Methods
    login,
    register,
    refresh,
    logout,
    clearError: () => setError(null),
  }
}
