import React, { useState, useRef } from 'react'
import { apiClient } from '../services/api'
import { Document } from '../types'
import '../styles/DocumentUpload.css'

interface DocumentUploadProps {
  onUploadSuccess: (document: Document) => void
  onUploadError: (error: string) => void
}

export default function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

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

  const MAX_FILE_SIZE = 25 * 1024 * 1024 // 25MB

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      return `Invalid file type. Allowed types: PDF, Word, Excel, Images (JPEG, PNG, TIFF)`
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is 25MB`
    }

    return null
  }

  const handleFilesSelect = (files: FileList | null) => {
    if (!files || files.length === 0) {
      setSelectedFiles([])
      setErrorMessage(null)
      return
    }

    const valid: File[] = []
    for (let i = 0; i < files.length; i++) {
      const f = files[i]
      const error = validateFile(f)
      if (error) {
        setErrorMessage(error)
        continue
      }
      valid.push(f)
    }

    if (valid.length === 0) {
      setSelectedFiles([])
      return
    }

    setSelectedFiles(valid)
    setErrorMessage(null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFilesSelect(e.target.files)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFilesSelect(files)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedFiles.length === 0) {
      setErrorMessage('Please select at least one file to upload')
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

      const results = await apiClient.uploadDocuments(selectedFiles)
      clearInterval(progressInterval)
      setUploadProgress(100)

      // Reset form
      setSelectedFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      if (Array.isArray(results)) {
        for (const r of results) {
          if (r && r.status === 'uploaded') {
            const mapped: Document = {
              id: r.document_id,
              name: r.filename,
              fileUrl: '',
              uploadedAt: new Date().toISOString(),
              owner_email: '',
              status: 'pending'
            }
            onUploadSuccess(mapped)
          } else if (r && r.error_message) {
            setErrorMessage(r.error_message)
            onUploadError(r.error_message)
          }
        }
      }

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

  const handleRemoveFile = (index: number) => {
    const next = [...selectedFiles]
    next.splice(index, 1)
    setSelectedFiles(next)
    if (next.length === 0 && fileInputRef.current) {
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
        <h3>📄 {selectedFiles.length > 1 ? 'Upload Documents' : 'Upload Document'}</h3>
        <p className="upload-description">
          Upload procurement documents (PDF, Word, Excel, Images) for processing
        </p>

        <form onSubmit={handleUpload}>
          {/* Drag and Drop Area */}
          <div
            className={`drop-zone ${isDragOver ? 'drag-over' : ''} ${selectedFiles.length ? 'has-file' : ''}`}
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
              multiple
            />
            {selectedFiles.length ? (
              <div className="file-selected">
                <div className="file-icon">📎</div>
                <div className="file-info">
                  <p className="file-name">{selectedFiles.map(f => f.name).join(', ')}</p>
                  <p className="file-size">
                    {selectedFiles.map(f => (f.size / 1024 / 1024).toFixed(2) + ' MB').join(' • ')}
                  </p>
                </div>
                {!isUploading && selectedFiles.map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleRemoveFile(idx)}
                    className="btn-remove"
                    aria-label="Remove file"
                  >
                    ✕
                  </button>
                ))}
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
                  Supported: PDF, Word, Excel, Images (Max 25MB per file)
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
            disabled={!selectedFiles.length || isUploading}
            className="btn-upload-submit"
          >
            {isUploading ? (
              <>
                <span className="spinner"></span> Uploading...
              </>
            ) : (
              (selectedFiles.length > 1 ? '⬆️ Upload Documents' : '⬆️ Upload Document')
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
            <li><strong>Max Size:</strong> 25 MB per file</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
