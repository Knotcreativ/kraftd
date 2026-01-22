/**
 * Schema API Endpoints
 */

import { apiGet, apiPost } from './client'
import type { Schema } from '../types'

/**
 * Generate schema for a conversion
 */
export async function generateSchema(conversionId: string): Promise<Schema> {
  return apiPost<Schema>('/schema/generate', {
    conversion_id: conversionId,
  })
}

/**
 * Get schema by ID
 */
export async function getSchema(schemaId: string): Promise<Schema> {
  return apiGet<Schema>(`/schema/${schemaId}`)
}

/**
 * Get latest schema for a conversion
 */
export async function getConversionSchema(conversionId: string): Promise<Schema> {
  return apiGet<Schema>(`/conversions/${conversionId}/schema`)
}

/**
 * Revise an existing schema
 */
export async function reviseSchema(payload: {
  schema_id: string
  instructions: string
}): Promise<Schema> {
  return apiPost<Schema>('/schema/revise', payload)
}

/**
 * Finalize a schema (lock it from further revisions)
 */
export async function finalizeSchema(schemaId: string): Promise<Schema> {
  return apiPost<Schema>('/schema/finalize', {
    schema_id: schemaId,
  })
}

/**
 * Get schema version history
 */
export async function getSchemaHistory(conversionId: string): Promise<Schema[]> {
  return apiGet<Schema[]>(`/conversions/${conversionId}/schema/history`)
}
