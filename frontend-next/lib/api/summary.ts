/**
 * Summary API Endpoints
 */

import { apiGet, apiPost } from './client'
import type { Summary } from '../types'

/**
 * Generate summary for a conversion
 */
export async function generateSummary(conversionId: string): Promise<Summary> {
  return apiPost<Summary>('/summary/generate', {
    conversion_id: conversionId,
  })
}

/**
 * Get summary by ID
 */
export async function getSummary(summaryId: string): Promise<Summary> {
  return apiGet<Summary>(`/summary/${summaryId}`)
}

/**
 * Get latest summary for a conversion
 */
export async function getConversionSummary(conversionId: string): Promise<Summary> {
  return apiGet<Summary>(`/conversions/${conversionId}/summary`)
}

/**
 * Regenerate summary with same conversion
 */
export async function regenerateSummary(conversionId: string): Promise<Summary> {
  return generateSummary(conversionId)
}
