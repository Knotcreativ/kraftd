# AI-Powered Download - Code Changes Reference

## Quick Reference: What Changed

This document shows the exact code additions and modifications for the AI-powered download feature.

---

## Frontend Changes

### 1. DocumentReviewDetail.tsx

#### New Type Definition (Line 45)
```typescript
type DocumentTemplate = 'standard' | 'executive_summary' | 'detailed_analysis' | 'financial_report' | 'technical_spec' | 'custom'
```

#### New State Variables (Lines 57-62)
```typescript
const [documentTemplate, setDocumentTemplate] = useState<DocumentTemplate>('standard')
const [templateCustomization, setTemplateCustomization] = useState('')
const [isDownloading, setIsDownloading] = useState(false)
```

#### Updated handleDownloadFile() (Lines 148-195)
```typescript
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
        documentTemplate,
        templateCustomization,
        use_ai_template_generation: true,
        aiSummary: aiSummary // Pass the AI summary for context
      }
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
```

#### New JSX Section (After AI Summary Display)
```tsx
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
```

### 2. api.ts

#### Updated downloadExportedFile() Method (Lines 225-251)
```typescript
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
```

### 3. DocumentReviewDetail.css

#### New Styles (Added before @media queries)
```css
/* Template Selection Styles */
.template-selection {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.template-selection h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.1rem;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.template-option {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.template-option input[type="radio"] {
  cursor: pointer;
  accent-color: #667eea;
  width: 18px;
  height: 18px;
}

.template-option:hover {
  border-color: #667eea;
  background: #f8f9fb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.template-option.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f3ff 0%, #e8ecff 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.template-name {
  display: block;
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
}

.template-desc {
  display: block;
  font-size: 0.8rem;
  color: #999;
  font-weight: 400;
}

.custom-template-input {
  background: #f8f9fb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.custom-template-input label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.custom-template-input .instructions-textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.95rem;
  resize: vertical;
}
```

---

## Backend Changes

### main.py

#### Updated Imports (Line 2)
```python
from fastapi.responses import JSONResponse, Response, FileResponse, StreamingResponse
```

#### Updated Export Endpoint (Lines 2165-2569)

The complete export endpoint now includes:

**New Parameters:**
```python
use_ai_template_generation = export_request.get("use_ai_template_generation", False)
document_template = export_request.get("document_template", "standard")
template_customization = export_request.get("template_customization", "")
ai_summary_from_phase1 = export_request.get("ai_summary", {})
```

**Phase 2: AI Template Generation Logic:**
```python
# PHASE 2: AI-Powered Template Generation (generates file with AI-formatted content)
if use_ai_template_generation and AGENT_AVAILABLE:
    logger.info(f"Phase 2: Generating AI-formatted document with template: {document_template}")
    try:
        agent = await get_or_init_agent()
        document_type = doc_record.get("document", {}).get("metadata", {}).get("document_type", "Unknown")
        
        # Build AI prompt for template-based formatting
        template_prompt = f"""
        You are formatting a {document_type} document using the "{document_template}" template.
        
        DOCUMENT DATA:
        {json.dumps(flat_data, indent=2, default=str)}
        
        AI SUMMARY (from previous review):
        {json.dumps(ai_summary_from_phase1, indent=2, default=str) if ai_summary_from_phase1 else "No summary available"}
        
        TEMPLATE STYLE: {document_template}
        """
        
        # Add custom template instructions if provided
        if document_template == 'custom' and template_customization:
            template_prompt += f"\n\nCUSTOM TEMPLATE INSTRUCTIONS:\n{template_customization}"
        else:
            # Add template-specific instructions
            template_instructions_map = {
                'standard': "Create a clean, professional document with clear sections",
                'executive_summary': "Create a concise high-level overview suitable for executives, 1-2 pages max",
                'detailed_analysis': "Create a comprehensive breakdown with detailed explanations and analysis of each data point",
                'financial_report': "Format data with emphasis on numbers, metrics, totals, and financial insights",
                'technical_spec': "Format data with emphasis on technical specifications, configurations, and implementation details"
            }
            template_prompt += f"\n\nTEMPLATE REQUIREMENTS:\n{template_instructions_map.get(document_template, '')}"
        
        template_prompt += f"\n\nOutput format for {format_type}: "
        if format_type == 'json':
            template_prompt += "Return as JSON with structured sections"
        elif format_type == 'csv':
            template_prompt += "Return as CSV with organized columns"
        elif format_type == 'excel':
            template_prompt += "Return structured data suitable for Excel spreadsheet"
        else:
            template_prompt += "Return as formatted text suitable for PDF report"
        
        # Get AI template generation
        template_response = await agent.process_message(
            message=template_prompt,
            conversation_id=f"{document_id}_template",
            document_context={"document_type": document_type, "template": document_template, "data": flat_data}
        )
        
        formatted_content = template_response.get("response", "")
        logger.info(f"Phase 2: AI template generation completed for document {document_id}")
        
        # Parse AI-formatted content for structured formats
        ai_formatted_data = flat_data
        if format_type == 'json':
            try:
                if "{" in formatted_content:
                    json_start = formatted_content.index("{")
                    json_end = formatted_content.rindex("}") + 1
                    ai_formatted_data = json.loads(formatted_content[json_start:json_end])
            except (json.JSONDecodeError, ValueError):
                logger.warning("Could not parse AI formatted JSON, using original data")
                ai_formatted_data = flat_data
        
    except Exception as template_error:
        logger.error(f"Phase 2: AI template generation error: {template_error}", exc_info=True)
        logger.warning("Continuing with standard formatting due to template generation error")
        ai_formatted_data = flat_data
else:
    ai_formatted_data = flat_data
```

**Enhanced File Generation:**
```python
# For JSON - includes template metadata
export_data = {
    "metadata": {
        "document_id": document_id,
        "template": document_template,
        "timestamp": datetime.datetime.now().isoformat(),
        "format": format_type
    },
    "data": ai_formatted_data,
    "transformation_instructions": transformation_instructions if transformation_instructions else None
}
if ai_summary_from_phase1:
    export_data["ai_review_summary"] = ai_summary_from_phase1

# For PDF - enhanced with metadata and table formatting
metadata_text = f"Document ID: {document_id[:8]} | Template: {document_template} | Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
story.append(Paragraph(metadata_text, styles['Normal']))

# Create table for data display
data_table = [["Field", "Value"]]
for key, value in ai_formatted_data.items():
    data_table.append([str(key), str(value)[:100] + ("..." if len(str(value)) > 100 else "")])

table = Table(data_table, colWidths=[2*inch, 4*inch])
```

**Updated Response:**
```python
# For Phase 1 (AI review), return JSON response
if use_ai_review and not use_ai_template_generation:
    return JSONResponse({
        "document_id": document_id,
        "status": "processed",
        "ai_summary": ai_summary if ai_summary else None,
        "export_format": format_type,
        "download_info": {
            "filename": filename,
            "format": format_type,
            "ready": True,
            "content_length": len(content)
        },
        "message": f"Document processed and ready to download as {format_type}"
    })

# For Phase 2 (template generation), return binary file content
return StreamingResponse(
    io.BytesIO(content),
    media_type=media_type,
    headers={"Content-Disposition": f"attachment; filename={filename}"}
)
```

---

## Summary of Changes

| File | Changes | Lines |
|------|---------|-------|
| DocumentReviewDetail.tsx | New state, handler, JSX | +140 |
| api.ts | Method signature update | +30 |
| DocumentReviewDetail.css | Template styling | +100 |
| main.py | Phase 2 AI logic | +400 |
| **Total** | | **~670** |

---

## Testing the Changes

### Before You Test
1. Both servers running (backend on 8000, frontend on 3000)
2. Database/Cosmos DB configured
3. Azure AI/KraftdAIAgent available

### Quick Test Steps
1. Upload document
2. View details
3. Edit some fields
4. Click "Export with AI Review"
5. Wait for AI summary
6. Select template from grid
7. Select format from dropdown
8. Click "Download Report"
9. File downloads with template name in filename

---

**Documentation:** See AI_POWERED_DOWNLOAD_FEATURE.md for full details
**Status:** Ready for Testing ✅
