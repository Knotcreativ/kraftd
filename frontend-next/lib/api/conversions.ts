/**
 * Conversions API Endpoints
 */

import { apiGet, apiPost, apiDelete } from './client'
import type { Conversion } from '../types'

/**
 * List all conversions for current user
 */
export async function getConversions(): Promise<Conversion[]> {
  return apiGet<Conversion[]>('/conversions')
}

/**
 * Get a specific conversion by ID
 */
export async function getConversion(id: string): Promise<Conversion> {
  return apiGet<Conversion>(`/conversions/${id}`)
}

/**
 * Create a new conversion
 */
export async function createConversion(payload: {
  document_name: string
  document_type: string
  source: string
}): Promise<Conversion> {
  return apiPost<Conversion>('/conversions', payload)
}

/**
 * Create conversion from file upload
 * Note: This would need a different approach for multipart/form-data
 * For now, assumes document is already stored and we're just creating the record
 */
export async function uploadConversion(file: File): Promise<Conversion> {
  // This would need a separate multipart/form-data implementation
  // For MVP, we'll use document_name from file
  return createConversion({
    document_name: file.name,
    document_type: file.type,
    source: 'uploaded',
  })
}

/**
 * Delete a conversion
 */
export async function deleteConversion(id: string): Promise<void> {
  return apiDelete(`/conversions/${id}`)
}

/**
 * Archive a conversion (soft delete)
 */
export async function archiveConversion(id: string): Promise<Conversion> {
  return apiPost<Conversion>(`/conversions/${id}/archive`, {})
}
