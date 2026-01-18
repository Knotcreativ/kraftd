import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Document } from '../types'
import '../styles/DocumentList.css'

interface DocumentListProps {
  documents: Document[]
  isLoading: boolean
  onRefresh: () => void
  onReview: (documentId: string) => void
  isReviewing: string | null
}

export default function DocumentList({ documents, isLoading, onRefresh, onReview, isReviewing }: DocumentListProps) {
  const navigate = useNavigate()
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-completed'
      case 'processing':
        return 'status-processing'
      case 'failed':
        return 'status-failed'
      case 'pending':
      default:
        return 'status-pending'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'processing':
        return '⏳'
      case 'failed':
        return '✕'
      case 'pending':
      default:
        return '⟳'
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf':
        return '📄'
      case 'doc':
      case 'docx':
        return '📝'
      case 'xls':
      case 'xlsx':
        return '📊'
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'tiff':
        return '🖼️'
      default:
        return '📎'
    }
  }

  return (
    <div className="document-list-container">
      <div className="list-header">
        <h3>📁 Uploaded Documents</h3>
        <button onClick={onRefresh} className="btn-refresh" disabled={isLoading}>
          🔄 Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <div className="loader"></div>
          <p>Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h4>No documents yet</h4>
          <p>Upload a document to get started with processing</p>
        </div>
      ) : (
        <div className="documents-grid">
          {documents.map((doc) => (
            <div key={doc.id} className="document-card">
              <div className="card-header">
                <div className="file-icon-large">{getFileIcon(doc.name)}</div>
                <div className={`status-badge ${getStatusColor(doc.status)}`}>
                  <span className="status-icon">{getStatusIcon(doc.status)}</span>
                  <span className="status-text">{doc.status}</span>
                </div>
              </div>

              <div className="card-body">
                <h4 className="document-name" title={doc.name}>
                  {doc.name}
                </h4>

                <div className="document-meta">
                  <div className="meta-item">
                    <span className="meta-label">Uploaded</span>
                    <span className="meta-value">{formatDate(doc.uploadedAt)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Owner</span>
                    <span className="meta-value">{doc.owner_email}</span>
                  </div>
                </div>
              </div>

              <div className="card-footer">
                <button 
                  className="btn-review"
                  onClick={() => onReview(doc.id)}
                  disabled={isReviewing === doc.id || doc.status === 'processing' || doc.status === 'completed'}
                >
                  {isReviewing === doc.id ? '⏳ Reviewing...' : '🔍 Review'}
                </button>
                <button 
                  className="btn-view"
                  onClick={() => navigate(`/dashboard/review/${doc.id}`)}
                >
                  👁️ View Details
                </button>
                <button className="btn-download">
                  ⬇️ Download
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
