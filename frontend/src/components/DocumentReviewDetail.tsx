import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../services/api'
import '../styles/DocumentReviewDetail.css'

interface ExtractedData {
  [key: string]: unknown
}

interface AISummary {
  executive_summary?: string
  key_findings?: string[]
  recommendations?: string[]
  risk_factors?: string[]
  action_items?: string[]
}

interface DocumentDetails {
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
    extracted_data: ExtractedData
    line_items?: unknown[]
    parties?: unknown[]
  }
}

type ExportFormat = 'json' | 'csv' | 'excel' | 'pdf'
type DocumentTemplate = 'standard' | 'executive_summary' | 'detailed_analysis' | 'financial_report' | 'technical_spec' | 'custom'

export default function DocumentReviewDetail() {
  const { documentId } = useParams<{ documentId: string }>()
  const navigate = useNavigate()
  
  const [details, setDetails] = useState<DocumentDetails | null>(null)
  const [editedData, setEditedData] = useState<ExtractedData>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [isProcessingWithAI, setIsProcessingWithAI] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('json')
  const [documentTemplate, setDocumentTemplate] = useState<DocumentTemplate>('standard')
  const [templateCustomization, setTemplateCustomization] = useState('')
  const [transformationInstructions, setTransformationInstructions] = useState('')
  const [exportMessage, setExportMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null)
  const [showAISummary, setShowAISummary] = useState(false)

  // Load document details on mount
  useEffect(() => {
    loadDocumentDetails()
  }, [documentId])

  const loadDocumentDetails = async () => {
    if (!documentId) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.getDocumentDetails(documentId)
      setDetails(response)
      // Initialize edited data with extracted data
      if (response.document.extracted_data) {
        setEditedData(response.document.extracted_data)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load document details'
      setError(message)
      console.error('Error loading document details:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDataEdit = (key: string, value: unknown) => {
    setEditedData(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleExport = async () => {
    if (!documentId || !details) return
    
    setIsExporting(true)
    setIsProcessingWithAI(true)
    setExportMessage(null)
    setAiSummary(null)
    
    try {
      // Request export with AI review enabled
      const exportResponse = await apiClient.exportDocument(documentId, {
        format: 'json',
        data: editedData,
        transformation_instructions: transformationInstructions,
        use_ai_review: true
      })
      
      // Extract AI summary from response
      if (exportResponse && exportResponse.ai_summary) {
        setAiSummary(exportResponse.ai_summary)
        setShowAISummary(true)
        
        setExportMessage({
          type: 'success',
          text: '✓ AI Review Complete - Ready to Download'
        })
      } else {
        setExportMessage({
          type: 'success',
          text: 'Document processed successfully'
        })
      }
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to export document'
      setExportMessage({
        type: 'error',
        text: `✕ ${message}`
      })
      console.error('Error exporting document:', err)
    } finally {
      setIsExporting(false)
      setIsProcessingWithAI(false)
    }
  }

  const handleDownloadFile = async () => {
    if (!documentId || !details) return
    
    setIsDownloading(true)
    setExportMessage(null)
    
    try {
      // Send to backend with AI template generation enabled
      const downloadResponse = await apiClient.downloadExportedFile(
        documentId,
        exportFormat,
        editedData,
        transformationInstructions,
        {
          documentTemplate: documentTemplate as string,
          templateCustomization,
          use_ai_template_generation: true,
          ...(aiSummary && { aiSummary })
        } as any
      )
      
      // Handle file download
      const url = window.URL.createObjectURL(new Blob([downloadResponse]))
      const link = document.createElement('a')
      link.href = url
      
      // Determine file extension and filename
      const ext = exportFormat === 'excel' ? 'xlsx' : exportFormat
      const timestamp = new Date().toISOString().split('T')[0]
      const filename = `${details.document_id.substring(0, 8)}_${documentTemplate}_${timestamp}.${ext}`
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      setExportMessage({
        type: 'success',
        text: `✓ File downloaded as ${exportFormat.toUpperCase()} (${documentTemplate} template)`
      })
      setTimeout(() => setExportMessage(null), 4000)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to download file'
      setExportMessage({
        type: 'error',
        text: `✕ ${message}`
      })
      console.error('Error downloading file:', err)
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="review-detail-container">
        <div className="loading-state">
          <div className="loader"></div>
          <p>Loading document details...</p>
        </div>
      </div>
    )
  }

  if (error || !details) {
    return (
      <div className="review-detail-container">
        <div className="error-state">
          <h3>Error Loading Document</h3>
          <p>{error || 'Document not found'}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            ← Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="review-detail-container">
      {/* Header Section */}
      <div className="review-header">
        <div className="header-top">
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            ← Back
          </button>
          <h1>📋 Document Review</h1>
          <div className="status-badge-large">
            {details.validation.requires_manual_review ? '⚠️ Needs Review' : '✓ Complete'}
          </div>
        </div>
      </div>

      {/* Summary Section */}
      <div className="summary-section">
        <h2>📊 Document Summary</h2>
        <div className="summary-grid">
          <div className="summary-card">
            <label>Document Type</label>
            <div className="value-large">{details.document_type}</div>
          </div>
          <div className="summary-card">
            <label>Processing Time</label>
            <div className="value-large">{details.processing_time_ms}ms</div>
          </div>
          <div className="summary-card">
            <label>Completeness</label>
            <div className="value-large score-bar">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${details.validation.completeness_score}%` }}
                ></div>
              </div>
              <span>{details.validation.completeness_score}%</span>
            </div>
          </div>
          <div className="summary-card">
            <label>Quality Score</label>
            <div className="value-large score-bar">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${details.validation.quality_score}%` }}
                ></div>
              </div>
              <span>{details.validation.quality_score}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Extraction Metrics */}
      <div className="metrics-section">
        <h3>🔍 Extraction Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">Fields Mapped</span>
            <span className="metric-value">{details.extraction_metrics.fields_mapped}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Inferences Made</span>
            <span className="metric-value">{details.extraction_metrics.inferences_made}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Line Items</span>
            <span className="metric-value">{details.extraction_metrics.line_items}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Parties Found</span>
            <span className="metric-value">{details.extraction_metrics.parties_found}</span>
          </div>
        </div>
      </div>

      {/* Editable Data Section */}
      <div className="data-section">
        <h2>✏️ Extracted Data (Editable)</h2>
        <div className="data-editor">
          {Object.entries(editedData).length === 0 ? (
            <p className="no-data">No extracted data available</p>
          ) : (
            <div className="data-fields">
              {Object.entries(editedData).map(([key, value]) => (
                <div key={key} className="data-field">
                  <label className="field-label">{key}</label>
                  {typeof value === 'string' ? (
                    <textarea
                      className="field-input"
                      value={value}
                      onChange={(e) => handleDataEdit(key, e.target.value)}
                      rows={3}
                    />
                  ) : typeof value === 'number' ? (
                    <input
                      type="number"
                      className="field-input"
                      value={value}
                      onChange={(e) => handleDataEdit(key, e.target.value)}
                    />
                  ) : (
                    <textarea
                      className="field-input"
                      value={JSON.stringify(value, null, 2)}
                      onChange={(e) => {
                        try {
                          handleDataEdit(key, JSON.parse(e.target.value))
                        } catch {
                          // Keep as string if invalid JSON
                          handleDataEdit(key, e.target.value)
                        }
                      }}
                      rows={4}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Export/Transformation Section */}
      <div className="export-section">
        <h2>📤 Export & Transform</h2>
        
        <div className="export-form">
          <div className="form-group">
            <label htmlFor="format-select">Output Format</label>
            <select
              id="format-select"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="format-select"
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="excel">Excel (XLSX)</option>
              <option value="pdf">PDF</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="instructions">Transformation Instructions (Optional)</label>
            <textarea
              id="instructions"
              className="instructions-textarea"
              placeholder="Describe any specific transformations or formatting you'd like applied to the data (e.g., 'Convert currency to USD', 'Merge name fields', 'Add calculated totals')"
              value={transformationInstructions}
              onChange={(e) => setTransformationInstructions(e.target.value)}
              rows={4}
            />
            <p className="hint-text">
              Provide instructions for how you'd like the data transformed before export
            </p>
          </div>

          {exportMessage && (
            <div className={`export-message ${exportMessage.type}`}>
              {exportMessage.text}
            </div>
          )}

          <button
            onClick={handleExport}
            disabled={isExporting || isProcessingWithAI}
            className="btn-export"
          >
            {isProcessingWithAI ? '⏳ AI Processing...' : isExporting ? '⏳ Exporting...' : '🤖 Export with AI Review'}
          </button>
        </div>
      </div>

      {/* AI Summary Section */}
      {showAISummary && aiSummary && (
        <div className="ai-summary-section">
          <h2>🧠 AI Review Summary</h2>
          
          {aiSummary.executive_summary && (
            <div className="summary-card">
              <h3>Executive Summary</h3>
              <p>{aiSummary.executive_summary}</p>
            </div>
          )}

          {aiSummary.key_findings && aiSummary.key_findings.length > 0 && (
            <div className="summary-card">
              <h3>🔍 Key Findings</h3>
              <ul className="findings-list">
                {aiSummary.key_findings.map((finding, idx) => (
                  <li key={idx}>{finding}</li>
                ))}
              </ul>
            </div>
          )}

          {aiSummary.recommendations && aiSummary.recommendations.length > 0 && (
            <div className="summary-card">
              <h3>💡 Recommendations</h3>
              <ul className="recommendations-list">
                {aiSummary.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {aiSummary.risk_factors && aiSummary.risk_factors.length > 0 && (
            <div className="summary-card risk-card">
              <h3>⚠️ Risk Factors</h3>
              <ul className="risk-list">
                {aiSummary.risk_factors.map((risk, idx) => (
                  <li key={idx}>{risk}</li>
                ))}
              </ul>
            </div>
          )}

          {aiSummary.action_items && aiSummary.action_items.length > 0 && (
            <div className="summary-card action-card">
              <h3>✅ Action Items</h3>
              <ul className="action-list">
                {aiSummary.action_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Download Section */}
          <div className="download-section">
            <p>AI review complete! Select template, format, and download your final report.</p>
            
            <div className="template-selection">
              <h3>📋 Document Template</h3>
              <div className="template-grid">
                <label className={`template-option ${documentTemplate === 'standard' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="standard"
                    checked={documentTemplate === 'standard'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">📄 Standard</span>
                  <span className="template-desc">Clean, professional layout</span>
                </label>

                <label className={`template-option ${documentTemplate === 'executive_summary' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="executive_summary"
                    checked={documentTemplate === 'executive_summary'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">👔 Executive Summary</span>
                  <span className="template-desc">High-level overview</span>
                </label>

                <label className={`template-option ${documentTemplate === 'detailed_analysis' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="detailed_analysis"
                    checked={documentTemplate === 'detailed_analysis'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">🔬 Detailed Analysis</span>
                  <span className="template-desc">Comprehensive breakdown</span>
                </label>

                <label className={`template-option ${documentTemplate === 'financial_report' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="financial_report"
                    checked={documentTemplate === 'financial_report'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">💰 Financial Report</span>
                  <span className="template-desc">Numbers and metrics</span>
                </label>

                <label className={`template-option ${documentTemplate === 'technical_spec' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="technical_spec"
                    checked={documentTemplate === 'technical_spec'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">⚙️ Technical Spec</span>
                  <span className="template-desc">Technical details</span>
                </label>

                <label className={`template-option ${documentTemplate === 'custom' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="template"
                    value="custom"
                    checked={documentTemplate === 'custom'}
                    onChange={(e) => setDocumentTemplate(e.target.value as DocumentTemplate)}
                  />
                  <span className="template-name">✨ Custom</span>
                  <span className="template-desc">Your specifications</span>
                </label>
              </div>

              {documentTemplate === 'custom' && (
                <div className="custom-template-input">
                  <label htmlFor="custom-spec">Describe your preferred template:</label>
                  <textarea
                    id="custom-spec"
                    className="instructions-textarea"
                    placeholder="e.g., 'Create a single-page summary with key metrics in table format, followed by action items'"
                    value={templateCustomization}
                    onChange={(e) => setTemplateCustomization(e.target.value)}
                    rows={3}
                  />
                </div>
              )}
            </div>

            <div className="download-actions">
              <div className="format-selector">
                <label htmlFor="download-format">Download Format:</label>
                <select
                  id="download-format"
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                  className="format-select"
                >
                  <option value="json">JSON</option>
                  <option value="csv">CSV</option>
                  <option value="excel">Excel (XLSX)</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
              <button
                onClick={handleDownloadFile}
                disabled={isDownloading}
                className="btn-download"
              >
                {isDownloading ? '⏳ Generating...' : '⬇️ Download Report'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Validation Info */}
      {details.validation.requires_manual_review && (
        <div className="warning-banner">
          <span>⚠️</span>
          <p>This document requires manual review. Some data may be incomplete or require verification.</p>
        </div>
      )}
    </div>
  )
}
