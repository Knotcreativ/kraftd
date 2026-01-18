import React, { useState, useRef } from 'react'
import { apiClient } from '../services/api'
import { Document } from '../types'
import '../styles/DocumentUpload.css'

interface DocumentUploadProps {
  onUploadSuccess: (document: Document) => void
  onUploadError: (error: string) => void
}

export default function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dragOverRef = useRef(false)

  const ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/tiff'
  ]

  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      return `Invalid file type. Allowed types: PDF, Word, Excel, Images (JPEG, PNG, TIFF)`
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is 50MB`
    }

    return null
  }

  const handleFileSelect = (file: File | null) => {
    if (!file) {
      setSelectedFile(null)
      setErrorMessage(null)
      return
    }

    const error = validateFile(file)
    if (error) {
      setErrorMessage(error)
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
    setErrorMessage(null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    handleFileSelect(file || null)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragOverRef.current = true
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragOverRef.current = false
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragOverRef.current = false

    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) {
      setErrorMessage('Please select a file to upload')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)
    setErrorMessage(null)

    try {
      // Simulate progress (since we don't have true progress tracking yet)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90))
      }, 100)

      const doc = await apiClient.uploadDocument(selectedFile)
      clearInterval(progressInterval)
      setUploadProgress(100)

      // Reset form
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      onUploadSuccess(doc)

      // Reset progress after a short delay
      setTimeout(() => {
        setUploadProgress(0)
      }, 1000)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Upload failed. Please try again.'
      setErrorMessage(errorMsg)
      onUploadError(errorMsg)
    } finally {
      setIsUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    setErrorMessage(null)
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="document-upload-container">
      <div className="upload-card">
        <h3>📄 Upload Document</h3>
        <p className="upload-description">
          Upload procurement documents (PDF, Word, Excel, Images) for processing
        </p>

        <form onSubmit={handleUpload}>
          {/* Drag and Drop Area */}
          <div
            className={`drop-zone ${dragOverRef.current ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleInputChange}
              disabled={isUploading}
              className="file-input-hidden"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.tiff"
            />

            {selectedFile ? (
              <div className="file-selected">
                <div className="file-icon">📎</div>
                <div className="file-info">
                  <p className="file-name">{selectedFile.name}</p>
                  <p className="file-size">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                {!isUploading && (
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    className="btn-remove"
                    aria-label="Remove file"
                  >
                    ✕
                  </button>
                )}
              </div>
            ) : (
              <div className="drop-instructions">
                <div className="drop-icon">📤</div>
                <p className="drop-text">Drag and drop your document here</p>
                <p className="drop-or">or</p>
                <button
                  type="button"
                  onClick={handleBrowseClick}
                  className="btn-browse"
                  disabled={isUploading}
                >
                  Browse Files
                </button>
                <p className="file-types">
                  Supported: PDF, Word, Excel, Images (Max 50MB)
                </p>
              </div>
            )}
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="upload-error">
              <span className="error-icon">⚠️</span>
              <p>{errorMessage}</p>
            </div>
          )}

          {/* Progress Bar */}
          {isUploading && (
            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="progress-text">{uploadProgress}%</p>
            </div>
          )}

          {/* Upload Button */}
          <button
            type="submit"
            disabled={!selectedFile || isUploading}
            className="btn-upload-submit"
          >
            {isUploading ? (
              <>
                <span className="spinner"></span> Uploading...
              </>
            ) : (
              '⬆️ Upload Document'
            )}
          </button>
        </form>

        {/* File Format Info */}
        <div className="format-info">
          <h4>Supported Formats</h4>
          <ul>
            <li><strong>Documents:</strong> PDF, Word (.doc, .docx)</li>
            <li><strong>Spreadsheets:</strong> Excel (.xls, .xlsx)</li>
            <li><strong>Images:</strong> JPEG, PNG, TIFF</li>
            <li><strong>Max Size:</strong> 50 MB per file</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
