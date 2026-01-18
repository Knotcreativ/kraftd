import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiClient } from '../services/api'
import { Document } from '../types'
import DocumentUpload from '../components/DocumentUpload'
import DocumentList from '../components/DocumentList'
import './Dashboard.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const { isAuthenticated, logout, user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isReviewing, setIsReviewing] = useState<string | null>(null)

  // Check authentication on mount
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    } else {
      loadDocuments()
    }
  }, [isAuthenticated, navigate])

  const loadDocuments = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs)
    } catch (err) {
      setError('Failed to load documents')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUploadSuccess = (doc: Document) => {
    setDocuments([doc, ...documents])
    setSuccessMessage(`✓ "${doc.name}" uploaded successfully!`)
    setTimeout(() => setSuccessMessage(null), 4000)
  }

  const handleUploadError = (errorMsg: string) => {
    setError(errorMsg)
    setTimeout(() => setError(null), 5000)
  }

  const handleReviewDocument = async (documentId: string) => {
    setIsReviewing(documentId)
    try {
      const result = await apiClient.reviewDocument(documentId)
      
      // Update document status to processing
      setDocuments(docs =>
        docs.map(doc =>
          doc.id === documentId
            ? { ...doc, status: 'processing' as const }
            : doc
        )
      )
      
      setSuccessMessage(`✓ Document review started! Processing: ${result.document_id.substring(0, 8)}...`)
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err) {
      setError(`Failed to review document: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setTimeout(() => setError(null), 5000)
    } finally {
      setIsReviewing(null)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>📊 KraftdIntel Dashboard</h1>
            {user && <p className="user-welcome">Welcome, {user.email}</p>}
          </div>
          <button onClick={handleLogout} className="btn-logout">
            🚪 Logout
          </button>
        </div>
      </header>

      <div className="dashboard-container">
        {/* Success Message */}
        {successMessage && (
          <div className="success-alert">
            <span className="alert-close" onClick={() => setSuccessMessage(null)}>✕</span>
            {successMessage}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-alert">
            <span className="alert-close" onClick={() => setError(null)}>✕</span>
            {error}
          </div>
        )}

        <div className="dashboard-grid">
          {/* Upload Section */}
          <div className="section upload-area">
            <DocumentUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>

          {/* Documents Section */}
          <div className="section documents-area">
            <DocumentList
              documents={documents}
              isLoading={isLoading}
              onRefresh={loadDocuments}
              onReview={handleReviewDocument}
              isReviewing={isReviewing}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
