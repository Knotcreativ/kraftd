import axios, { AxiosError, AxiosInstance } from 'axios'
import { AuthTokens, Document, Workflow } from '../types'

// Support both production and local development URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000/api/v1'
    : 'https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1')

class ApiClient {
  private client: AxiosInstance
  private csrfToken: string = ''

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      },
      // PHASE 8: Enable credentials to send/receive cookies
      withCredentials: true
    })

    // Request interceptor to add auth token or CSRF token
    this.client.interceptors.request.use((config) => {
      // PHASE 8: Try to get token from localStorage (fallback for backward compatibility)
      const token = localStorage.getItem('accessToken')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      // PHASE 8: Add CSRF token to POST/PUT/DELETE requests
      if (this.csrfToken && (config.method === 'post' || config.method === 'put' || config.method === 'delete')) {
        config.headers['X-CSRF-Token'] = this.csrfToken
      }
      
      return config
    })

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          const refreshToken = localStorage.getItem('refreshToken')
          if (refreshToken) {
            try {
              const response = await this.client.post('/auth/refresh', {
                refreshToken
              })
              const { accessToken } = response.data
              localStorage.setItem('accessToken', accessToken)
              
              // Retry original request
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${accessToken}`
                return this.client(error.config)
              }
            } catch (refreshError) {
              localStorage.removeItem('accessToken')
              localStorage.removeItem('refreshToken')
              window.location.href = '/login'
            }
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async register(email: string, password: string, acceptTerms: boolean = false, acceptPrivacy: boolean = false, name?: string) {
    const response = await this.client.post<AuthTokens>('/auth/register', {
      email,
      password,
      acceptTerms,
      acceptPrivacy,
      name: name || email.split('@')[0],
      marketingOptIn: false
    })
    return response.data
  }

  async login(email: string, password: string) {
    const response = await this.client.post<AuthTokens>('/auth/login', {
      email,
      password
    })
    return response.data
  }

  async refreshToken(refreshToken: string) {
    const response = await this.client.post<AuthTokens>('/auth/refresh', {
      refreshToken
    })
    return response.data
  }

  // Email verification endpoints
  async verifyEmail(token: string) {
    const response = await this.client.post('/auth/verify-email', {
      token
    })
    return response.data
  }

  async resendVerification(email: string) {
    const response = await this.client.post('/auth/resend-verification', {
      email
    })
    return response.data
  }

  // Phase 9: Password Recovery endpoints
  async forgotPassword(email: string) {
    const response = await this.client.post('/auth/forgot-password', {
      email
    })
    return response.data
  }

  async resetPassword(token: string, newPassword: string, confirmPassword: string) {
    const response = await this.client.post('/auth/reset-password', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword
    })
    return response.data
  }

  // Document endpoints
  async uploadDocument(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async uploadDocuments(files: File[]) {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    const response = await this.client.post<any[]>('/docs/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async getDocument(id: string) {
    const response = await this.client.get<Document>(`/documents/${id}`)
    return response.data
  }

  async listDocuments() {
    const response = await this.client.get<{ documents: Document[]; total_count: number }>('/documents')
    return response.data.documents
  }

  async updateDocument(id: string, data: Partial<Document>) {
    const response = await this.client.put<Document>(`/documents/${id}`, data)
    return response.data
  }

  async deleteDocument(id: string) {
    await this.client.delete(`/documents/${id}`)
  }

  async reviewDocument(documentId: string) {
    const response = await this.client.post<{ 
      document_id: string
      status: string
      extracted_data: Record<string, unknown>
      confidence_score: number
      processing_time_ms: number
    }>(`/docs/extract?document_id=${documentId}`)
    return response.data
  }

  async getDocumentDetails(documentId: string) {
    const response = await this.client.get<{
      document_id: string
      status: string
      document_type: string
      processing_time_ms: number
      extraction_metrics: {
        fields_mapped: number
        inferences_made: number
        line_items: number
        parties_found: number
      }
      validation: {
        completeness_score: number
        quality_score: number
        overall_score: number
        ready_for_processing: boolean
        requires_manual_review: boolean
      }
      document: {
        metadata: {
          document_type: string
        }
        extracted_data: Record<string, unknown>
        line_items?: unknown[]
        parties?: unknown[]
      }
    }>(`/docs/${documentId}`)
    return response.data
  }

  async exportDocument(documentId: string, options: {
    format: 'json' | 'csv' | 'excel' | 'pdf'
    data: Record<string, unknown>
    transformation_instructions?: string
    use_ai_review?: boolean
  }): Promise<any> {
    try {
      // First request gets the response with AI summary (JSON)
      const response = await this.client.post<any>(
        `/docs/${documentId}/export`,
        options,
        {
          responseType: 'json'  // Get JSON response first for AI summary
        }
      )
      return response.data
    } catch (error) {
      console.error('Error exporting document:', error)
      throw error
    }
  }

  async downloadExportedFile(
    documentId: string,
    format: 'json' | 'csv' | 'excel' | 'pdf',
    data: Record<string, unknown>,
    instructions?: string,
    templateOptions?: {
      documentTemplate: string
      templateCustomization?: string
      use_ai_template_generation?: boolean
      aiSummary?: Record<string, unknown>
    }
  ): Promise<ArrayBuffer> {
    const response = await this.client.post<ArrayBuffer>(
      `/docs/${documentId}/export`,
      {
        format,
        data,
        transformation_instructions: instructions || '',
        use_ai_review: false,
        use_ai_template_generation: templateOptions?.use_ai_template_generation || false,
        document_template: templateOptions?.documentTemplate || 'standard',
        template_customization: templateOptions?.templateCustomization || '',
        ai_summary: templateOptions?.aiSummary || {}
      },
      {
        responseType: 'arraybuffer'
      }
    )
    return response.data
  }

  // Workflow endpoints
  async startWorkflow(documentId: string) {
    const response = await this.client.post<Workflow>('/workflows/start', {
      documentId
    })
    return response.data
  }

  async getWorkflow(id: string) {
    const response = await this.client.get<Workflow>(`/workflows/${id}`)
    return response.data
  }

  async updateWorkflowStatus(id: string, status: string) {
    const response = await this.client.put<Workflow>(`/workflows/${id}/status`, {
      status
    })
    return response.data
  }

  // PHASE 8: CSRF Token Management
  async getCsrfToken(): Promise<string> {
    try {
      const response = await this.client.get<{ csrf_token: string }>('/auth/csrf-token')
      this.csrfToken = response.data.csrf_token
      return this.csrfToken
    } catch (error) {
      console.error('Failed to get CSRF token:', error)
      throw error
    }
  }

  setCsrfToken(token: string): void {
    this.csrfToken = token
  }

  getCsrfTokenSync(): string {
    return this.csrfToken
  }

  // Phase 10: Event History endpoints
  async getEventPrices(startDate: string, endDate: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get<any>('/events/prices', {
      params: { start_date: startDate, end_date: endDate, limit, offset }
    })
    return response.data
  }

  async getEventAlerts(startDate: string, endDate: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get<any>('/events/alerts', {
      params: { start_date: startDate, end_date: endDate, limit, offset }
    })
    return response.data
  }

  async getEventAnomalies(startDate: string, endDate: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get<any>('/events/anomalies', {
      params: { start_date: startDate, end_date: endDate, limit, offset }
    })
    return response.data
  }

  async getEventSignals(startDate: string, endDate: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get<any>('/events/signals', {
      params: { start_date: startDate, end_date: endDate, limit, offset }
    })
    return response.data
  }

  async getEventTrends(startDate: string, endDate: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get<any>('/events/trends', {
      params: { start_date: startDate, end_date: endDate, limit, offset }
    })
    return response.data
  }

  async getEventStats(startDate: string, endDate: string) {
    const response = await this.client.get<any>('/events/stats', {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  }

  async getAggregatedEvents(groupBy: 'day' | 'week' | 'month' | 'hour', startDate: string, endDate: string) {
    const response = await this.client.get<any>('/events/aggregate', {
      params: { group_by: groupBy, start_date: startDate, end_date: endDate }
    })
    return response.data
  }

  // User preferences endpoints
  async getPreferences() {
    const response = await this.client.get<any>('/users/preferences')
    return response.data
  }

  async updatePreferences(preferences: Record<string, any>) {
    const response = await this.client.put<any>('/users/preferences', preferences)
    return response.data
  }

  async getAlertThresholds() {
    const response = await this.client.get<any>('/users/alert-thresholds')
    return response.data
  }

  async updateAlertThresholds(thresholds: Record<string, any>) {
    const response = await this.client.put<any>('/users/alert-thresholds', thresholds)
    return response.data
  }

  // Health check
  async getHealth() {
    const response = await this.client.get('/health')
    return response.status === 200
  }
}

export const apiClient = new ApiClient()
