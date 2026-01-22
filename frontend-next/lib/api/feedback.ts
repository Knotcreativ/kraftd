/**
 * Feedback API Endpoints
 */

import { apiGet, apiPost } from './client'
import type { Feedback } from '../types'

export type TargetType = 'schema' | 'summary' | 'output'

/**
 * Submit feedback for a result
 */
export async function submitFeedback(payload: {
  conversion_id: string
  target_type: TargetType
  target_id: string
  rating: number
  comments: string
}): Promise<Feedback> {
  return apiPost<Feedback>('/feedback', payload)
}

/**
 * Get feedback for a conversion
 */
export async function getConversionFeedback(conversionId: string): Promise<Feedback[]> {
  return apiGet<Feedback[]>(`/conversions/${conversionId}/feedback`)
}

/**
 * Get all feedback (admin)
 */
export async function getAllFeedback(): Promise<Feedback[]> {
  return apiGet<Feedback[]>('/feedback')
}

/**
 * Get feedback for a specific target
 */
export async function getTargetFeedback(
  targetType: TargetType,
  targetId: string
): Promise<Feedback[]> {
  return apiGet<Feedback[]>(`/feedback?target_type=${targetType}&target_id=${targetId}`)
}
