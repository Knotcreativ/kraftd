import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../services/api'
import { Document } from '../types'
import './DocumentDetail.css'

interface ExtractedData {
  documentType?: string
  date?: string
  parties?: Record<string, any>
  lineItems?: Array<Record<string, any>>
  totals?: Record<string, any>
  metadata?: Record<string, any>
  recommendations?: string[]
  completenessScore?: number
}

export default function DocumentDetail() {
  const { documentId } = useParams<{ documentId: string }>()
  const navigate = useNavigate()
  
  const [document, setDocument] = useState<Document | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel' | 'csv'>('excel')

  useEffect(() => {
    if (documentId) {
      loadDocumentDetails()
    }
  }, [documentId])

  const loadDocumentDetails = async () => {
    setIsLoading(true)
    setError(null)
    try {
      if (!documentId) {
        setError('Document ID is required')
        return
      }

      const doc = await apiClient.getDocument(documentId)
      setDocument(doc)

      // Extract data from the document response
      // The document object contains extracted fields
      if (doc && typeof doc === 'object') {
        setExtractedData({
          documentType: (doc as any).document_type || 'Unknown',
          date: (doc as any).date || (doc as any).issue_date || '',
          parties: (doc as any).parties || {},
          lineItems: (doc as any).line_items || (doc as any).lineItems || [],
          totals: (doc as any).totals || {},
          metadata: (doc as any).metadata || {},
          recommendations: (doc as any).recommendations || [],
          completenessScore: (doc as any).completeness_score || (doc as any).completenessScore || 0
        })
      }
    } catch (err) {
      setError('Failed to load document details')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartWorkflow = async () => {
    try {
      if (!documentId) {
        setError('Document ID is required')
        return
      }
      // Navigate to workflow selection page (can be implemented later)
      navigate(`/workflow/${documentId}`)
    } catch (err) {
      setError('Failed to start workflow')
      console.error(err)
    }
  }

  const handleExport = async () => {
    try {
      if (!documentId) {
        setError('Document ID is required')
        return
      }
      
      setIsExporting(true)
      // Call export endpoint using api client - use the standard method pattern
      const response = await (apiClient as any).client.get(`/documents/${documentId}/output`, {
        params: { format: exportFormat },
        responseType: 'blob'
      })

      {/* Create download link */}
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = (document as any).createElement('a')
      link.href = url
      link.setAttribute('download', `document_${documentId.substring(0, 8)}.${exportFormat === 'excel' ? 'xlsx' : exportFormat}`)
      (document as any).body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
    } catch (err) {
      setError('Failed to export document')
      console.error(err)
    } finally {
      setIsExporting(false)
    }
  }

  const getCompletenessColor = (score: number) => {
    if (score >= 80) return '#4CAF50' // Green
    if (score >= 60) return '#FFC107' // Amber
    return '#F44336' // Red
  }

  if (isLoading) {
    return (
      <div className="document-detail">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading document details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-detail">
        <div className="error-container">
          <button className="btn-back" onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </button>
          <div className="error-message">{error}</div>
          <button className="btn-retry" onClick={loadDocumentDetails}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!document || !extractedData) {
    return (
      <div className="document-detail">
        <div className="error-container">
          <button className="btn-back" onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </button>
          <div className="error-message">Document not found</div>
        </div>
      </div>
    )
  }

  return (
    <div className="document-detail">
      {/* Header Section */}
      <div className="detail-header">
        <button className="btn-back" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
        <h1>{document.name || 'Document Details'}</h1>
        <div className="header-meta">
          <span className={`status-badge ${document.status}`}>
            {document.status?.toUpperCase() || 'UNKNOWN'}
          </span>
          <span className="upload-date">
            Uploaded {new Date(document.uploadedAt).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="detail-container">
        {/* Completeness Score Card */}
        <div className="completeness-card">
          <h3>Data Completeness</h3>
          <div className="completeness-visual">
            <div className="circular-progress">
              <svg viewBox="0 0 100 100" width="120" height="120">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" strokeWidth="8" />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke={getCompletenessColor(extractedData.completenessScore || 0)}
                  strokeWidth="8"
                  strokeDasharray={`${((extractedData.completenessScore || 0) / 100) * 282.6} 282.6`}
                  style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                />
                <text x="50" y="50" textAnchor="middle" dy=".3em" fontSize="24" fontWeight="bold">
                  {extractedData.completenessScore || 0}%
                </text>
              </svg>
            </div>
            <div className="completeness-info">
              <p>
                {extractedData.completenessScore && extractedData.completenessScore >= 80
                  ? '✓ Excellent - All critical data present'
                  : extractedData.completenessScore && extractedData.completenessScore >= 60
                    ? '⚠ Good - Some data missing'
                    : '✗ Incomplete - Several fields missing'}
              </p>
            </div>
          </div>
        </div>

        {/* Document Metadata */}
        <div className="metadata-card">
          <h3>Document Information</h3>
          <div className="metadata-grid">
            <div className="metadata-item">
              <label>Document Type</label>
              <span>{extractedData.documentType || 'Unknown'}</span>
            </div>
            <div className="metadata-item">
              <label>Document Date</label>
              <span>{extractedData.date ? new Date(extractedData.date).toLocaleDateString() : 'Not found'}</span>
            </div>
            {extractedData.metadata && Object.keys(extractedData.metadata).length > 0 && (
              <div className="metadata-item full-width">
                <label>Additional Metadata</label>
                <div className="metadata-details">
                  {Object.entries(extractedData.metadata).map(([key, value]) => (
                    <div key={key} className="metadata-entry">
                      <span className="meta-key">{key}:</span>
                      <span className="meta-value">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Parties Information */}
        {extractedData.parties && Object.keys(extractedData.parties).length > 0 && (
          <div className="parties-card">
            <h3>Parties</h3>
            <div className="parties-grid">
              {Object.entries(extractedData.parties).map(([partyType, partyData]) => (
                <div key={partyType} className="party-item">
                  <h4>{partyType}</h4>
                  <div className="party-details">
                    {typeof partyData === 'object' && partyData !== null ? (
                      Object.entries(partyData).map(([field, value]) => (
                        <div key={field} className="party-field">
                          <span className="field-label">{field}:</span>
                          <span className="field-value">{String(value)}</span>
                        </div>
                      ))
                    ) : (
                      <p>{String(partyData)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Line Items Table */}
        {extractedData.lineItems && extractedData.lineItems.length > 0 && (
          <div className="line-items-card">
            <h3>Line Items</h3>
            <div className="table-wrapper">
              <table className="line-items-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {extractedData.lineItems.map((item, index) => (
                    <tr key={index}>
                      <td>{item.item || item.name || item.description || `Item ${index + 1}`}</td>
                      <td>{item.quantity || item.qty || '-'}</td>
                      <td>{item.unit_price || item.unitPrice || item.price || '-'}</td>
                      <td>{item.total || item.lineTotal || '-'}</td>
                      <td className="description-cell">{item.notes || item.remarks || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Totals Section */}
        {extractedData.totals && Object.keys(extractedData.totals).length > 0 && (
          <div className="totals-card">
            <h3>Totals</h3>
            <div className="totals-grid">
              {Object.entries(extractedData.totals).map(([totalType, totalValue]) => (
                <div key={totalType} className="total-item">
                  <span className="total-label">{totalType}:</span>
                  <span className="total-value">{String(totalValue)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations Section */}
        {extractedData.recommendations && extractedData.recommendations.length > 0 && (
          <div className="recommendations-card">
            <h3>Recommendations</h3>
            <ul className="recommendations-list">
              {extractedData.recommendations.map((rec, index) => (
                <li key={index} className="recommendation-item">
                  <span className="rec-icon">→</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing Fields Warning */}
        {extractedData.completenessScore && extractedData.completenessScore < 100 && (
          <div className="missing-fields-card">
            <h3>Missing or Incomplete Fields</h3>
            <p>The following fields could not be automatically extracted:</p>
            <ul className="missing-fields-list">
              {extractedData.completenessScore < 80 && (
                <>
                  <li>Critical supplier information (partial)</li>
                  <li>Complete pricing details</li>
                  <li>Delivery terms and conditions</li>
                </>
              )}
              {extractedData.completenessScore < 60 && (
                <>
                  <li>Payment terms</li>
                  <li>Tax information</li>
                  <li>Signature or approval marks</li>
                </>
              )}
            </ul>
            <p className="missing-note">You can manually review and update these fields in the workflow.</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="detail-actions">
        <div className="action-group">
          <button className="btn-action btn-primary" onClick={handleStartWorkflow}>
            Start Workflow
          </button>
          <button className="btn-action btn-secondary" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </button>
        </div>

        <div className="action-group">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as any)}
            disabled={isExporting}
            className="export-select"
          >
            <option>Select format...</option>
            <option>excel</option>
            <option>pdf</option>
            <option>csv</option>
          </select>
          <button
            className="btn-action btn-secondary"
            onClick={handleExport}
            disabled={isExporting}
          >
            {isExporting ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>
    </div>
  )
}
