import axios, { AxiosError, AxiosInstance } from 'axios'
import { AuthTokens, Document, Workflow } from '../types'

// Support both production and local development URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000/api/v1'
    : 'https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1')

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
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
              const response = await this.client.post('/auth/refresh-token', {
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
    const response = await this.client.post<AuthTokens>('/auth/refresh-token', {
      refreshToken
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

  async getDocument(id: string) {
    const response = await this.client.get<Document>(`/documents/${id}`)
    return response.data
  }

  async listDocuments() {
    const response = await this.client.get<Document[]>('/documents')
    return response.data
  }

  async updateDocument(id: string, data: Partial<Document>) {
    const response = await this.client.put<Document>(`/documents/${id}`, data)
    return response.data
  }

  async deleteDocument(id: string) {
    await this.client.delete(`/documents/${id}`)
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

  // Health check
  async getHealth() {
    const response = await this.client.get('/health')
    return response.status === 200
  }
}

export const apiClient = new ApiClient()
