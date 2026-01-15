export interface User {
  id: string
  email: string
  name: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number
}

export interface Document {
  id: string
  name: string
  fileUrl: string
  uploadedAt: string
  owner_email: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

export interface Workflow {
  id: string
  documentId: string
  status: 'initiated' | 'in_progress' | 'approved' | 'rejected' | 'completed'
  currentStep: number
  steps: WorkflowStep[]
}

export interface WorkflowStep {
  step: number
  name: string
  status: 'pending' | 'completed' | 'failed'
  timestamp?: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}
