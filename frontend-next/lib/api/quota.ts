/**
 * Quota API Endpoints
 */

import { apiGet } from './client'
import type { Quota } from '../types'

/**
 * Get quota information for current user
 */
export async function getQuota(): Promise<Quota> {
  return apiGet<Quota>('/quota')
}

/**
 * Check if user can perform an action
 */
export async function checkQuotaLimit(action: 'conversions' | 'exports' | 'api_calls'): Promise<boolean> {
  try {
    const quota = await getQuota()

    switch (action) {
      case 'conversions':
        return quota.conversions_used < quota.conversions_limit
      case 'exports':
        return quota.exports_used < quota.exports_limit
      case 'api_calls':
        return quota.api_calls_used < quota.api_calls_limit
      default:
        return false
    }
  } catch {
    return false
  }
}

/**
 * Get quota usage percentage
 */
export function getUsagePercentage(
  used: number,
  limit: number
): number {
  if (limit === 0) return 0
  return Math.round((used / limit) * 100)
}

/**
 * Check if quota is nearly full
 */
export function isQuotaNearlyFull(used: number, limit: number, threshold = 80): boolean {
  return getUsagePercentage(used, limit) >= threshold
}

/**
 * Check if quota is exceeded
 */
export function isQuotaExceeded(used: number, limit: number): boolean {
  return used >= limit
}
