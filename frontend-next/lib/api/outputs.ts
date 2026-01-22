/**
 * Outputs API Endpoints
 */

import { apiGet, apiPost } from './client'
import type { Output } from '../types'

export type OutputFormat = 'json' | 'csv' | 'text' | 'markdown'

/**
 * Generate output in specified format
 */
export async function generateOutput(payload: {
  conversion_id: string
  format: OutputFormat
}): Promise<Output> {
  return apiPost<Output>('/outputs/generate', payload)
}

/**
 * Get output by ID
 */
export async function getOutput(outputId: string): Promise<Output> {
  return apiGet<Output>(`/outputs/${outputId}`)
}

/**
 * List outputs for a conversion
 */
export async function getConversionOutputs(conversionId: string): Promise<Output[]> {
  return apiGet<Output[]>(`/conversions/${conversionId}/outputs`)
}

/**
 * Download output as file
 */
export async function downloadOutput(outputId: string): Promise<Blob> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/outputs/${outputId}/download`,
    {
      headers: {
        Authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('kraftd_jwt') : ''}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error('Failed to download output')
  }

  return response.blob()
}

/**
 * Export output as file in browser
 */
export function exportOutput(content: string, filename: string, format: OutputFormat): void {
  const mimeTypes: Record<OutputFormat, string> = {
    json: 'application/json',
    csv: 'text/csv',
    text: 'text/plain',
    markdown: 'text/markdown',
  }

  const blob = new Blob([content], { type: mimeTypes[format] })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
