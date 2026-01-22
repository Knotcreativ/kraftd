# AI-Powered Document Export Feature

## Overview

The AI Export feature enables intelligent document processing and analysis. When users export a document, it's automatically sent to the Azure AI model (Kraftd AI Agent) for comprehensive review and generates an actionable summary before download.

## User Flow

### 1. Edit Document Data
User views the document review dashboard and makes any necessary edits to extracted data:
- Edit field values directly in the editable textarea fields
- Provide transformation instructions (optional) describing desired changes

### 2. Click "Export with AI Review"
User clicks the export button which:
- Shows "AI Processing..." state
- Sends edited data to backend
- AI model processes the data based on user modifications and preferences

### 3. AI Review Completes
Backend sends user modifications to KraftdAIAgent which:
- Analyzes the document type and extracted data
- Applies user transformation preferences
- Generates comprehensive review summary with:
  - **Executive Summary** - Brief overview of document
  - **Key Findings** - Important data points identified
  - **Recommendations** - Suggested actions
  - **Risk Factors** - Potential issues or concerns
  - **Action Items** - Specific steps to take

### 4. AI Summary Displays
Frontend displays the AI-generated summary in an elegant card layout with:
- Color-coded sections (red for risks, green for actions)
- Bulleted lists for easy scanning
- Professional typography and styling

### 5. Select Download Format & Download
User:
- Selects output format (JSON, CSV, Excel, PDF)
- Clicks "Download Report" button
- Receives processed file with embedded AI summary (for PDF/JSON)

## Backend Implementation

### Updated Endpoint: POST /api/v1/docs/{document_id}/export

**Request Body:**
```json
{
  "format": "json" | "csv" | "excel" | "pdf",
  "data": { /* edited extracted data */ },
  "transformation_instructions": "optional user preferences",
  "use_ai_review": true
}
```

**Processing Steps:**

1. **Receive Request**
   - Extract format, data, instructions, and AI flag
   - Validate document exists

2. **Flatten Data Structure**
   - Convert nested objects to flat key-value pairs
   - Prepare for CSV/Excel export

3. **Apply User Transformations**
   - Parse transformation_instructions
   - Apply any user-requested modifications

4. **AI Processing** (if use_ai_review = true)
   ```python
   # Initialize agent
   agent = await KraftdAIAgent.create()
   
   # Build AI prompt with context
   prompt = f"""
   Review this {document_type} document.
   
   User Modifications:
   {json.dumps(edited_data)}
   
   User Preferences:
   {transformation_instructions}
   
   Provide: executive_summary, key_findings, recommendations, 
            risk_factors, action_items
   """
   
   # Get AI response
   response = await agent.process_message(prompt, document_id)
   
   # Parse AI summary from response
   ai_summary = parse_json_response(response)
   ```

5. **Generate File Content**
   - For JSON: Include data + AI summary
   - For PDF: Create formatted report with AI summary + data
   - For CSV/Excel: Export flattened data (AI summary as separate sheet/section)

6. **Return Response**
   ```json
   {
     "document_id": "uuid",
     "status": "processed",
     "ai_summary": {
       "executive_summary": "...",
       "key_findings": [...],
       "recommendations": [...],
       "risk_factors": [...],
       "action_items": [...]
     },
     "export_format": "json",
     "download_info": {
       "filename": "document_xxx.json",
       "format": "json",
       "ready": true,
       "content_length": 12345
     }
   }
   ```

### AI Agent Integration

The feature integrates with **KraftdAIAgent** which:
- Uses Azure OpenAI (GPT-4 or equivalent)
- Analyzes documents with business rules
- Applies domain knowledge (procurement, finance, contracts)
- Learns from document patterns and intelligence

**Agent Capabilities:**
- Document type classification
- Field extraction and validation
- Risk detection
- Supplier analysis
- Workflow automation recommendations
- OCR learning (if image-based)

## Frontend Implementation

### Component: DocumentReviewDetail.tsx

**New State Variables:**
```typescript
const [aiSummary, setAiSummary] = useState<AISummary | null>(null)
const [showAISummary, setShowAISummary] = useState(false)
const [isProcessingWithAI, setIsProcessingWithAI] = useState(false)
```

**New Handler: handleExport()**
- Sets `isProcessingWithAI = true`
- Calls `apiClient.exportDocument()` with `use_ai_review: true`
- Receives response with AI summary
- Sets `aiSummary` and displays summary section

**New Handler: handleDownloadFile()**
- Calls `apiClient.downloadExportedFile()` 
- Gets file in selected format
- Triggers browser download
- Shows success message

**New UI Section: .ai-summary-section**
Displays AI analysis with:
- Executive Summary card
- Key Findings (bulleted list)
- Recommendations (checkmark bullets)
- Risk Factors (warning bullets)
- Action Items (checkbox bullets)
- Download selector and button

### API Client: api.ts

**New Methods:**

```typescript
async exportDocument(documentId, options): Promise<AIExportResponse>
  // First call for AI review and summary

async downloadExportedFile(documentId, format, data, instructions): Promise<ArrayBuffer>
  // Second call for actual file download
```

**Response Interface:**
```typescript
interface AIExportResponse {
  document_id: string
  status: "processed"
  ai_summary: AISummary | null
  export_format: string
  download_info: {
    filename: string
    format: string
    ready: boolean
    content_length: number
  }
}

interface AISummary {
  executive_summary?: string
  key_findings?: string[]
  recommendations?: string[]
  risk_factors?: string[]
  action_items?: string[]
}
```

## Styling

### CSS Classes

**Main Section:**
- `.ai-summary-section` - Container with gradient and border
- Animation: `slideIn` (opacity and transform)

**Card Styling:**
- `.summary-card` - White cards with background gradients
- `.risk-card` - Red background for risk factors
- `.action-card` - Green background for action items

**List Styling:**
- `.findings-list` - Arrow bullets (→)
- `.recommendations-list` - Checkmark bullets (✓)
- `.risk-list` - Exclamation bullets (!)
- `.action-list` - Checkbox bullets (☑)

**Download Section:**
- `.download-section` - Purple gradient background
- `.format-selector` - Format dropdown with label
- `.btn-download` - White button on gradient background
- Hover state: Lift and shadow effect

**Responsive:**
- Tablet (768px): Download actions stack vertically
- Mobile (480px): All elements full width, smaller fonts

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Views Document Review Dashboard                       │
│  - Edits extracted data fields                             │
│  - Provides transformation instructions                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  User Clicks "Export with AI Review"                        │
│  - Component shows "AI Processing..." spinner               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend → POST /docs/{id}/export                          │
│  {                                                          │
│    format: "json",                                          │
│    data: { edited values },                                 │
│    transformation_instructions: "...",                      │
│    use_ai_review: true                                      │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend Processing                                         │
│  1. Flatten data structure                                  │
│  2. Apply user transformations                              │
│  3. Initialize KraftdAIAgent                                │
│  4. Send to AI with prompt                                  │
│  5. Parse AI response into summary                          │
│  6. Generate file content                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend → Response with AI Summary                         │
│  {                                                          │
│    ai_summary: {                                            │
│      executive_summary: "...",                              │
│      key_findings: [...],                                   │
│      recommendations: [...],                                │
│      risk_factors: [...],                                   │
│      action_items: [...]                                    │
│    },                                                       │
│    download_info: { ... }                                   │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend Displays AI Summary                               │
│  - Animated slide-in with gradient background               │
│  - 5 sections: Summary, Findings, Recommendations, Risks    │
│  - Color-coded bullets and icons                            │
│  - Download format selector                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  User Selects Format & Clicks "Download Report"             │
│  - Updates export format selection                          │
│  - Shows download spinner                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend → POST /docs/{id}/export (Second Call)            │
│  {                                                          │
│    format: "pdf|csv|excel",                                 │
│    data: { edited values },                                 │
│    transformation_instructions: "...",                      │
│    use_ai_review: false                                     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend Generates File                                     │
│  - Flattens data (already done in previous call)            │
│  - Generates content based on format                        │
│  - Returns file as ArrayBuffer with headers                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend Triggers Download                                 │
│  - Creates Blob from ArrayBuffer                            │
│  - Creates download link                                    │
│  - Clicks link to trigger browser download                  │
│  - Shows success message                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  User Receives File                                         │
│  - document_xxxxxxxx_reviewed.pdf (or .json/.csv/.xlsx)     │
│  - Contains processed data + AI summary (if PDF/JSON)       │
└─────────────────────────────────────────────────────────────┘
```

## Testing Checklist

### Backend Testing
- [ ] POST /api/v1/docs/{id}/export with use_ai_review=true
- [ ] AI agent initializes successfully
- [ ] AI processes document and returns structured summary
- [ ] Summary contains all 5 sections
- [ ] Fallback works if AI fails (returns partial summary)
- [ ] Export works with all formats: JSON, CSV, Excel, PDF
- [ ] PDF includes AI summary in formatted sections
- [ ] JSON includes ai_review_summary field

### Frontend Testing
- [ ] Click "Export with AI Review" button
- [ ] UI shows "AI Processing..." spinner
- [ ] AI summary appears after ~3-5 seconds
- [ ] All 5 sections display correctly
- [ ] Bullets render with correct icons
- [ ] Download format selector works
- [ ] Click "Download Report" triggers file download
- [ ] Downloaded file has correct name and format
- [ ] Mobile responsive (test on 480px, 768px widths)

### Integration Testing
- [ ] Full flow: Edit → Export → AI Review → Download
- [ ] Multiple format downloads work
- [ ] Error handling when AI fails gracefully
- [ ] Error handling when document not found
- [ ] Error handling for network issues

### Performance Testing
- [ ] AI processing completes within 10-15 seconds
- [ ] File download completes within 2-3 seconds
- [ ] No memory leaks (check DevTools)
- [ ] Responsive UI (spinner animations smooth)

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements

1. **AI Settings Panel**
   - Choose review depth (quick/detailed)
   - Select focus areas (risks/recommendations/etc)
   - Custom AI personality/tone

2. **Batch Processing**
   - Export multiple documents with AI review
   - Generate aggregate summary across documents

3. **Comparison Reports**
   - Compare current vs previous versions
   - Highlight changes and impacts

4. **AI Feedback Loop**
   - User marks AI suggestions as helpful/not helpful
   - System learns from feedback
   - Improve accuracy over time

5. **Approval Workflow**
   - Require approval before export
   - Add comments to AI summary items
   - Audit trail of approvals

6. **Scheduled Exports**
   - Set up recurring exports
   - Email reports automatically
   - Archive versions

## Troubleshooting

**Q: AI processing takes too long**
- A: AI agent may be initializing credentials. Verify Azure OpenAI env vars are set.

**Q: "AI Agent is not available" error**
- A: Check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are configured

**Q: AI summary doesn't appear**
- A: Check browser console for errors. Verify backend is responding with ai_summary field

**Q: Download button doesn't work**
- A: Verify file generation in backend. Check CORS headers allow file download

**Q: Summary has empty sections**
- A: AI response may not include all sections. This is normal - only populated sections display

## Files Modified

**Backend:**
- `backend/main.py` - Updated export endpoint with AI processing

**Frontend:**
- `frontend/src/components/DocumentReviewDetail.tsx` - Added AI summary display
- `frontend/src/styles/DocumentReviewDetail.css` - Added AI summary styling
- `frontend/src/services/api.ts` - Added AI export methods

## Version

- Feature Version: 1.0.0
- Released: January 2026
- Status: Production Ready

