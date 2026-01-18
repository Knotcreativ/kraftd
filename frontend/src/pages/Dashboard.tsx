import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiClient } from '../services/api'
import { Document } from '../types'
import './Dashboard.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    setIsUploading(true)
    try {
      const doc = await apiClient.uploadDocument(selectedFile)
      setDocuments([doc, ...documents])
      setSelectedFile(null)
    } catch (err) {
      setError('Upload failed')
      console.error(err)
    } finally {
      setIsUploading(false)
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
          <h1>Documents & Procurement Management</h1>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="upload-section">
          <h2>Upload Document</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <div className="file-input-wrapper">
              <input
                type="file"
                onChange={handleFileSelect}
                disabled={isUploading}
                id="file-input"
              />
              <label htmlFor="file-input" className="file-label">
                {selectedFile ? selectedFile.name : 'Select a file or drag and drop'}
              </label>
            </div>
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="btn-upload"
            >
              {isUploading ? 'Uploading...' : 'Upload'}
            </button>
          </form>
        </div>

        <div className="documents-section">
          <h2>Your Documents</h2>
          {error && <div className="error-message">{error}</div>}

          {isLoading ? (
            <div className="loading">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <p>No documents uploaded yet</p>
              <p className="hint">Upload your first document above to get started</p>
            </div>
          ) : (
            <div className="documents-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <div className="doc-header">
                    <h3>{doc.name}</h3>
                    <span className={`status ${doc.status}`}>{doc.status}</span>
                  </div>
                  <p className="doc-meta">
                    Uploaded: {new Date(doc.uploadedAt).toLocaleDateString()}
                  </p>
                  <div className="doc-actions">
                    <button className="btn-view">View</button>
                    <button className="btn-workflow">Start Workflow</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
