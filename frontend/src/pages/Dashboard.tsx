import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiClient } from '../services/api'
import { Document } from '../types'
import DocumentUpload from '../components/DocumentUpload'
import DocumentList from '../components/DocumentList'
import './Dashboard.css'

// Dashboard Statistics Card Component
interface StatCard {
  label: string
  value: string | number
  icon: string
  color: string
  trend?: string
}

const StatCard: React.FC<StatCard> = ({ label, value, icon, color, trend }) => (
  <div className={`stat-card stat-${color}`}>
    <div className="stat-icon">{icon}</div>
    <div className="stat-content">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {trend && <p className="stat-trend">{trend}</p>}
    </div>
  </div>
)

// Activity Feed Component
interface Activity {
  id: string
  type: 'upload' | 'process' | 'export' | 'delete'
  document: string
  timestamp: string
  status: 'success' | 'processing' | 'error'
}

const ActivityFeed: React.FC<{ activities: Activity[] }> = ({ activities }) => {
  const getActivityIcon = (type: string) => {
    const icons: Record<string, string> = {
      upload: '📤',
      process: '⚙️',
      export: '📥',
      delete: '🗑️'
    }
    return icons[type] || '📝'
  }

  return (
    <div className="activity-feed">
      <h3>Recent Activity</h3>
      <div className="activity-list">
        {activities.length === 0 ? (
          <p className="empty-message">No recent activity</p>
        ) : (
          activities.map(activity => (
            <div key={activity.id} className={`activity-item activity-${activity.status}`}>
              <span className="activity-icon">{getActivityIcon(activity.type)}</span>
              <div className="activity-details">
                <p className="activity-text">
                  {activity.type.charAt(0).toUpperCase() + activity.type.slice(1)}: {activity.document}
                </p>
                <p className="activity-time">{activity.timestamp}</p>
              </div>
              <span className={`activity-badge ${activity.status}`}>
                {activity.status === 'success' ? '✓' : activity.status === 'processing' ? '⟳' : '!'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { isAuthenticated, logout, user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isReviewing, setIsReviewing] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'documents'>('overview')
  const [stats, setStats] = useState({
    totalDocuments: 0,
    processed: 0,
    pending: 0,
    exported: 0
  })

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
      
      // Calculate statistics
      const processed = docs.filter(d => d.status === 'completed').length
      const pending = docs.filter(d => d.status === 'processing' || d.status === 'pending').length
      
      setStats({
        totalDocuments: docs.length,
        processed,
        pending,
        exported: 0
      })
    } catch (err) {
      setError('Failed to load documents')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUploadSuccess = (doc: Document) => {
    setDocuments([doc, ...documents])
    setStats(prev => ({ ...prev, totalDocuments: prev.totalDocuments + 1 }))
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
      
      setStats(prev => ({
        ...prev,
        pending: prev.pending + 1,
        totalDocuments: Math.max(prev.totalDocuments, documents.length)
      }))
      
      setSuccessMessage(`✓ Document review started! Processing: ${result.document_id.substring(0, 8)}...`)
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err) {
      setError(`Failed to review document: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setTimeout(() => setError(null), 5000)
    } finally {
      setIsReviewing(null)
    }
  }

  const handleDeleteDocument = async (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await apiClient.deleteDocument(documentId)
        const deletedDoc = documents.find(d => d.id === documentId)
        setDocuments(documents.filter(d => d.id !== documentId))
        
        // Update stats
        if (deletedDoc) {
          setStats(prev => ({
            ...prev,
            totalDocuments: prev.totalDocuments - 1,
            processed: deletedDoc.status === 'completed' ? prev.processed - 1 : prev.processed,
            pending: (deletedDoc.status === 'processing' || deletedDoc.status === 'pending') ? prev.pending - 1 : prev.pending,
            exported: prev.exported
          }))
        }
        
        setSuccessMessage('✓ Document deleted successfully')
        setTimeout(() => setSuccessMessage(null), 4000)
      } catch (err) {
        setError(`Failed to delete document: ${err instanceof Error ? err.message : 'Unknown error'}`)
        setTimeout(() => setError(null), 5000)
      }
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>📊 Kraftd Docs</h1>
            {user && <p className="user-welcome">Welcome back, {user.email.split('@')[0]}! 👋</p>}
          </div>
          <button onClick={handleLogout} className="btn-logout">
            🚪 Logout
          </button>
        </div>
      </header>

      <div className="dashboard-container">
        {/* Alerts */}
        {successMessage && (
          <div className="success-alert">
            <span className="alert-close" onClick={() => setSuccessMessage(null)}>✕</span>
            {successMessage}
          </div>
        )}
        {error && (
          <div className="error-alert">
            <span className="alert-close" onClick={() => setError(null)}>✕</span>
            {error}
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="dashboard-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📈 Overview
          </button>
          <button
            className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📄 Documents ({documents.length})
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-section">
            {/* Statistics Cards */}
            <div className="stats-grid">
              <StatCard
                label="Total Documents"
                value={stats.totalDocuments}
                icon="📁"
                color="blue"
                trend="All time"
              />
              <StatCard
                label="Processed"
                value={stats.processed}
                icon="✅"
                color="green"
                trend={`${stats.totalDocuments > 0 ? Math.round((stats.processed / stats.totalDocuments) * 100) : 0}% complete`}
              />
              <StatCard
                label="Processing"
                value={stats.pending}
                icon="⏳"
                color="yellow"
              />
              <StatCard
                label="Exported"
                value={stats.exported}
                icon="📥"
                color="purple"
              />
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <h3>Quick Actions</h3>
              <div className="actions-grid">
                <button className="action-btn" onClick={() => setActiveTab('documents')}>
                  <span className="action-icon">➕</span>
                  <span>Upload Document</span>
                </button>
                <button className="action-btn">
                  <span className="action-icon">📊</span>
                  <span>View Analytics</span>
                </button>
                <button className="action-btn">
                  <span className="action-icon">⚙️</span>
                  <span>Settings</span>
                </button>
                <button className="action-btn">
                  <span className="action-icon">❓</span>
                  <span>Help & Guides</span>
                </button>
              </div>
            </div>

            {/* Activity Feed */}
            <ActivityFeed 
              activities={documents.slice(0, 5).map((doc, idx) => ({
                id: doc.id,
                type: 'upload',
                document: doc.name,
                timestamp: new Date(doc.uploadedAt).toLocaleDateString(),
                status: doc.status === 'completed' ? 'success' : doc.status === 'processing' ? 'processing' : 'error'
              }))}
            />
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="documents-section">
            {/* Upload Section */}
            <div className="upload-section">
              <h2>Upload Contract</h2>
              <DocumentUpload 
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </div>

            {/* Documents List */}
            {isLoading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Loading your documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="empty-state">
                <p className="empty-icon">📄</p>
                <h3>No documents yet</h3>
                <p>Upload your first contract to get started with AI-powered analysis!</p>
              </div>
            ) : (
              <DocumentList
                documents={documents}
                isLoading={isLoading}
                onRefresh={loadDocuments}
                onReview={handleReviewDocument}
                isReviewing={isReviewing}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
