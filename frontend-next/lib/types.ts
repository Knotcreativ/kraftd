/**
 * Shared Types for KRAFTD Frontend & Backend Integration
 */

// User Types
export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  created_at: string
  updated_at: string
}

// Conversion Types
export interface Conversion {
  id: string
  user_email: string
  document_name: string
  document_type: string
  source: string
  file_path?: string
  size_bytes?: number
  created_at: string
  updated_at: string
  status: 'active' | 'archived'
}

// Schema Types
export interface Schema {
  id: string
  conversion_id: string
  user_email: string
  version: number
  content: Record<string, unknown>
  status: 'draft' | 'final'
  created_at: string
  finalized_at?: string
}

export interface SchemaRevisionRequest {
  schema_id: string
  instructions: string
}

// Summary Types
export interface Summary {
  id: string
  conversion_id: string
  user_email: string
  content: string
  key_points?: string[]
  generated_at: string
}

// Output Types
export interface Output {
  id: string
  conversion_id: string
  user_email: string
  format: 'json' | 'csv' | 'text' | 'markdown'
  content: string
  generated_at: string
}

// Feedback Types
export interface Feedback {
  id: string
  user_email: string
  conversion_id: string
  target_type: 'schema' | 'summary' | 'output'
  target_id: string
  rating: number
  comments: string
  created_at: string
}

// Quota Types
export interface QuotaTier {
  tier: 'free' | 'pro' | 'enterprise'
  conversions_limit: number
  exports_limit: number
  api_calls_limit: number
}

export interface Quota {
  id: string
  user_email: string
  tier: 'free' | 'pro' | 'enterprise'
  conversions_used: number
  conversions_limit: number
  exports_used: number
  exports_limit: number
  api_calls_used: number
  api_calls_limit: number
  period_start: string
  period_end: string
  created_at: string
  updated_at: string
}

export interface QuotaExceededError {
  message: string
  quota_type: 'conversions' | 'exports' | 'api_calls'
  current: number
  limit: number
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  timestamp?: string
}

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: Record<string, unknown>
}

// Auth Types
export interface AuthToken {
  token: string
  expires_in?: number
  user_email?: string
}

// Pagination
export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  data: T[]
  meta: PaginationMeta
}
