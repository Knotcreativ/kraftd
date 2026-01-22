/**
 * useQuota Hook - Track and manage quota usage
 */

'use client'

import { useQuery } from '@tanstack/react-query'
import { getQuota, getUsagePercentage, isQuotaNearlyFull, isQuotaExceeded } from '@/lib/api/quota'
import type { Quota } from '@/lib/types'

export function useQuota() {
  const {
    data: quota,
    isLoading,
    error,
    refetch,
  } = useQuery<Quota>({
    queryKey: ['quota'],
    queryFn: getQuota,
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  })

  // Calculate usage percentages
  const conversionsUsagePercent = quota
    ? getUsagePercentage(quota.conversions_used, quota.conversions_limit)
    : 0

  const exportsUsagePercent = quota
    ? getUsagePercentage(quota.exports_used, quota.exports_limit)
    : 0

  const apiCallsUsagePercent = quota
    ? getUsagePercentage(quota.api_calls_used, quota.api_calls_limit)
    : 0

  // Check limits
  const conversionsExceeded = quota ? isQuotaExceeded(quota.conversions_used, quota.conversions_limit) : false
  const exportsExceeded = quota ? isQuotaExceeded(quota.exports_used, quota.exports_limit) : false
  const apiCallsExceeded = quota ? isQuotaExceeded(quota.api_calls_used, quota.api_calls_limit) : false

  // Check if nearly full
  const conversionsNearlyFull = quota ? isQuotaNearlyFull(quota.conversions_used, quota.conversions_limit) : false
  const exportsNearlyFull = quota ? isQuotaNearlyFull(quota.exports_used, quota.exports_limit) : false
  const apiCallsNearlyFull = quota ? isQuotaNearlyFull(quota.api_calls_used, quota.api_calls_limit) : false

  return {
    quota,
    isLoading,
    error,
    refetch,
    // Usage percentages
    conversionsUsagePercent,
    exportsUsagePercent,
    apiCallsUsagePercent,
    // Exceeded flags
    conversionsExceeded,
    exportsExceeded,
    apiCallsExceeded,
    // Nearly full flags
    conversionsNearlyFull,
    exportsNearlyFull,
    apiCallsNearlyFull,
    // Convenience checks
    canConvert: !conversionsExceeded,
    canExport: !exportsExceeded,
  }
}
