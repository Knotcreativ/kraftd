# KraftdIntel Frontend - Structure & UX Analysis
## Document Conversion User Experience Review

---

## 1. MAIN PAGES

### **Dashboard.tsx** (Primary Landing Page)
- **Purpose**: Central hub after login; displays document list and upload interface
- **Key Features**:
  - Document list with status indicators (pending, processing, completed, failed)
  - Inline document upload component
  - Document review/action buttons
  - Logout and user welcome
- **State Management**:
  - `documents[]` array loaded from API
  - `isLoading`, `error`, `successMessage` for UI feedback
  - `isReviewing` tracks current document being processed
- **User Flow**: Login → Dashboard → Upload/View Documents
- **API Calls**: 
  - `listDocuments()` on mount
  - `reviewDocument(id)` for triggering analysis
  - `uploadDocument(file)` via DocumentUpload child component

### **DocumentReviewDetail.tsx** (Review & Export Page)
- **Purpose**: View extracted data, AI analysis, and export options
- **Key Features**:
  - Document metadata display (type, processing time, completeness score)
  - Extracted data viewer (editable fields)
  - AI summary section (executive summary, findings, recommendations)
  - Export controls (format: JSON/CSV/Excel/PDF, template selection)
  - Download button after export completes
- **State Management**:
  - `details` - full document details from API
  - `editedData` - user-modified extracted data
  - `aiSummary` - AI-generated insights (loaded separately)
  - `exportFormat`, `documentTemplate` - export customization
  - `isExporting`, `isDownloading` - loading states
- **User Flow**: Dashboard → Click document → Review details → Export → Download
- **API Calls**:
  - `getDocumentDetails(id)` on mount
  - `exportDocument(id, options)` with AI review enabled
  - Download endpoint after export ready

### **Login.tsx** (Authentication Entry)
- **Purpose**: User authentication and registration
- **Key Features**:
  - Email/password login form
  - "Forgot password" link
  - Registration link
  - Email verification flow
- **State Management**: Handled via `AuthContext`
- **User Flow**: Login → Email Verification (optional) → Dashboard

### **PreferencesPage.tsx** (Settings/Configuration)
- **Purpose**: User preferences and configuration
- **Tabs**:
  1. **Alert Settings** - Alert thresholds, severity levels
  2. **Notifications** - Email, SMS, in-app toggles
  3. **Display** - Theme (light/dark/auto), animations, sidebar
  4. **Data & Privacy** - Data retention, analytics opt-in
- **State Management**:
  - `preferences` object synced with API
  - `activeTab` for tab navigation
  - `isSaving`, `isLoading` for async operations
- **API Calls**:
  - `getPreferences()` on mount
  - `updatePreferences(data)` on save

### **StreamingDashboard.tsx** (Real-Time Monitoring)
- **Purpose**: Real-time data visualization
- **Key Features**:
  - WebSocket-powered live updates
  - Price trends, risk alerts, supplier signals
  - Anomaly detection visualization
  - Health checks
- **Components Used**: 
  - `PriceDashboard`, `RiskAlerts`, `SupplierSignals`, `AnomalyDetection`, `TrendAnalysis`
- **Not Primary for Document Conversion** (more for procurement analytics)

### **AnalyticsPage.tsx** (Historical Analytics)
- **Purpose**: Historical data analysis and reporting
- **Not Primary for Document Conversion** (advanced feature)

---

## 2. KEY COMPONENTS FOR DOCUMENT CONVERSION FLOW

### **DocumentUpload.tsx** ⭐ (Core Upload Component)
**Responsibility**: File selection, validation, upload initiation

**Features**:
- **Drag-and-drop zone** (with visual feedback on hover)
- **File type validation**:
  - Allowed: PDF, Word (DOCX), Excel (XLSX), Images (JPEG, PNG, TIFF)
  - Max size: 50MB
- **Upload progress bar** (simulated with 10% increments)
- **File preview** (filename, size display before upload)
- **Error handling** with user-friendly messages

**State**:
```typescript
selectedFile: File | null
isUploading: boolean
uploadProgress: 0-100
errorMessage: string | null
```

**UX Flow**:
1. User drops file or clicks "Browse"
2. File validated (type, size)
3. File name shown with size
4. User clicks "Upload"
5. Progress bar animates 0% → 90% → 100%
6. Success callback updates parent Dashboard
7. Form resets for next upload

**Issue Identified**:
- ⚠️ **Progress is simulated** (comment: "Simulate progress since we don't have true progress tracking yet")
- Real upload progress not tracked (no `onUploadProgress` callback)

### **DocumentList.tsx** (Document Gallery)
**Responsibility**: Display uploaded documents with status badges

**Features**:
- Document cards with: name, status, upload date
- Status badges: 
  - 🟡 PENDING (yellow)
  - 🔵 PROCESSING (blue, animated)
  - 🟢 COMPLETED (green)
  - 🔴 FAILED (red)
- Click to review (navigates to `/dashboard/review/:documentId`)
- Empty state message if no documents

**State**: Receives `documents[]` as props from parent Dashboard

### **DocumentReviewDetail.tsx** ⭐ (Review & Export Component)
**Responsibility**: Display extraction results and enable export

**Features**:
- **Document Metadata Display**:
  - Document type, processing time
  - Extraction metrics (fields mapped, line items, parties found)
  - Validation scores (completeness, quality, overall)
- **Extracted Data Viewer**:
  - Key-value pairs displayed
  - Inline editing capability (editable fields)
- **AI Summary Section** (collapsible):
  - Executive summary
  - Key findings (bullet points)
  - Recommendations
  - Risk factors
  - Action items
- **Export Controls**:
  - Format dropdown (JSON, CSV, Excel, PDF)
  - Template selector (Standard, Executive Summary, Detailed Analysis, etc.)
  - Custom transformation instructions (textarea)
  - "Use AI Review" toggle
- **Two-Step Export Flow**:
  1. Click "Export" → AI review runs → "Ready to Download" message
  2. Click "Download" → File downloaded

**State**:
```typescript
details: DocumentDetails | null  // Full document data
editedData: ExtractedData        // User-modified fields
aiSummary: AISummary | null      // AI-generated insights
isExporting: boolean             // "Processing with AI..." state
isDownloading: boolean           // "Downloading..." state
exportFormat: 'json' | 'csv' | 'excel' | 'pdf'
documentTemplate: string         // Template selection
```

**UX Flow**:
1. Page loads → API call `getDocumentDetails(id)`
2. User views/edits extracted data
3. User selects export format & template
4. User clicks "Export" → `exportDocument(id, options)` with `use_ai_review: true`
5. AI summary loads → "Ready to Download" message
6. User clicks "Download" → File streams to browser
7. Success message displayed

**Issues Identified**:
- ⚠️ **Two-click export** (Export → Download) adds friction for simple use case
- ⚠️ **AI review always enabled** (no quick download option)
- ⚠️ **No progress indicator during export generation** (just boolean `isExporting`)

### **ExportComplete.tsx** (Export Success Screen)
**Responsibility**: Confirmation screen after export completes

**Features**:
- Success message
- Download button
- Link back to dashboard
- Export metadata display

**Not Heavily Used** (export flow embedded in DocumentReviewDetail now)

### **LoadingSpinner.tsx** (Reusable Loader)
**Responsibility**: Visual loading indicator

**Props**:
- `size`: 'small' | 'medium' | 'large'
- `message`: Optional text under spinner
- `fullScreen`: Boolean (overlay entire screen)

**Used Throughout**: DocumentUpload, DocumentReviewDetail, Dashboard

### **ErrorBoundary.tsx** (Global Error Handler)
**Responsibility**: Catch React errors and display fallback UI

**Features**:
- Catches component errors
- Displays friendly error message
- "Try Again" button

---

## 3. FRONTEND ↔ BACKEND COMMUNICATION

### **API Client Architecture**

#### **File: services/api.ts** (Central API Client)

**Setup**:
```typescript
class ApiClient {
  private client: AxiosInstance  // Axios HTTP client
  private csrfToken: string      // CSRF protection
  
  constructor() {
    // Base URL: Production or localhost:8000
    // Timeout: 10 seconds
    // withCredentials: true (for cookies)
  }
}
```

**Request Interceptor**:
- Adds JWT token from `localStorage.getItem('accessToken')`
- Adds CSRF token to POST/PUT/DELETE requests
- Header: `Authorization: Bearer <token>`

**Response Interceptor**:
- Detects 401 Unauthorized
- Attempts token refresh with `refreshToken`
- Retries original request with new token
- Redirects to /login if refresh fails

**Methods** (20+ endpoints):

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `register()` | POST /auth/register | Create account |
| `login()` | POST /auth/login | Authenticate user |
| `refreshToken()` | POST /auth/refresh | Renew access token |
| `uploadDocument(file)` | POST /documents/upload | Upload file |
| `listDocuments()` | GET /documents | Get user's documents |
| `getDocumentDetails(id)` | GET /documents/{id} | Get document metadata |
| `reviewDocument(id)` | POST /documents/{id}/review | Trigger AI analysis |
| `exportDocument(id, opts)` | POST /documents/{id}/export | Generate export |
| `getPreferences()` | GET /preferences | Get user settings |
| `updatePreferences(data)` | PUT /preferences | Save user settings |
| `getCsrfToken()` | GET /auth/csrf-token | Get CSRF token |

**Error Handling**:
- All methods wrapped in try-catch
- AxiosError converted to user-friendly messages
- Network errors handled gracefully

**Example Flow (Upload)**:
```
DocumentUpload.tsx
  ↓ handleUpload()
  ↓ apiClient.uploadDocument(file)
  ↓ POST http://localhost:8000/api/v1/documents/upload
  ↓ multipart/form-data with file
  ↓ Backend returns: { id, name, status, uploadedAt }
  ↓ Success callback updates Dashboard state
```

### **Authentication Context**

#### **File: context/AuthContext.tsx** (Global Auth State)

**Provides**:
```typescript
{
  isAuthenticated: boolean      // User logged in?
  isLoading: boolean            // Auth check in progress?
  error: string | null          // Auth error message
  user: User | null             // Current user data
  token: string | null          // Access token
  login(email, password): Promise<void>
  register(email, password, ...): Promise<void>
  logout(): void
  clearError(): void
}
```

**Token Storage**:
- `localStorage.setItem('accessToken', token)`
- `localStorage.setItem('refreshToken', token)`
- `localStorage.setItem('expiresAt', timestamp)`

**Token Expiry**: Not automatically checked (relies on backend 401 for refresh trigger)

**Issue**:
- ⚠️ No auto-logout on token expiration (passive expiry only)
- ⚠️ Tokens stored in localStorage (XSS risk if app compromised)

---

## 4. WEBSOCKET REAL-TIME UPDATES

### **File: hooks/useWebSocket.ts** (WebSocket Hook)

**Purpose**: Subscribe to real-time event streams from backend

**Event Types Supported**:
1. **PriceUpdate** - Price changes, trends, volatility
2. **RiskAlert** - Critical/high/medium/low alerts
3. **SupplierSignal** - Supplier health changes
4. **AnomalyDetected** - Statistical anomalies
5. **TrendChange** - Trend direction shifts
6. **HealthCheck** - Server heartbeat

**Hook API**:
```typescript
const { 
  isConnected,       // WebSocket connected?
  isConnecting,      // Connection in progress?
  error,             // Connection error
  events,            // Array of received events
  lastEvent,         // Most recent event
  connect,           // Manual connect
  disconnect,        // Manual disconnect
  subscribe          // Subscribe to specific filters
} = useWebSocket({
  url: 'wss://...', 
  topic: 'alerts',
  filters: { severity: 'HIGH' },
  autoConnect: true,
  reconnectAttempts: 5,
  reconnectInterval: 3000
})
```

**Reconnection Logic**:
- Automatically reconnects on connection loss
- Exponential backoff (3s → 6s → 12s → max 60s)
- Max 5 attempts before giving up

**Used In**:
- `StreamingDashboard.tsx` - Real-time price/alert monitoring
- `RiskAlerts.tsx` - Live alert notifications
- `PriceDashboard.tsx` - Live price updates

**NOT Used for Document Upload**:
- ⚠️ **Document processing does NOT push WebSocket updates**
- User must manually refresh or poll to see status changes
- No "Processing Complete" notification

**WebSocket Endpoint Pattern**:
```
wss://backend/ws/alerts?token=<jwt>
wss://backend/ws/prices?token=<jwt>
wss://backend/ws/signals?token=<jwt>
wss://backend/ws/anomalies?token=<jwt>
wss://backend/ws/trends?token=<jwt>
```

**Authentication**: JWT token passed as query parameter

---

## 5. UX FRICTION POINTS FOR B2C DOCUMENT CONVERSION

### **🔴 Critical Issues**

| Issue | Impact | User Pain |
|-------|--------|-----------|
| **1. Two-click export** (Export → Download) | High | "Why do I need to click twice? Just give me the file!" |
| **2. No real-time status updates** | High | "Is my document still processing? Do I need to refresh?" |
| **3. Simulated upload progress** | Medium | "Is it actually uploading or frozen at 90%?" |
| **4. AI review forced on every export** | Medium | "I just want a quick JSON download, why wait for AI?" |
| **5. No drag-to-upload on dashboard** | Medium | Must use dedicated upload component (extra clicks) |
| **6. Complex review page** | Medium | Too many options for simple conversion task |
| **7. Technical terminology** | Medium | "Completeness score", "line items", "parties found" confusing |
| **8. No inline preview** | High | Can't preview extracted data before clicking into review page |
| **9. No bulk upload** | Medium | Must upload one file at a time |
| **10. Email verification required** | Medium | Barrier to quick trial (B2C expects instant access) |

### **🟡 Moderate Friction**

| Issue | Impact | User Pain |
|-------|--------|-----------|
| **11. Multi-page navigation** | Medium | Upload → Dashboard → Review → Export (4 steps) |
| **12. No keyboard shortcuts** | Low | Power users want Ctrl+U (upload), Ctrl+E (export) |
| **13. Status not color-coded enough** | Low | Text-only status harder to scan |
| **14. No recent uploads shortcut** | Low | Must scroll through full list |
| **15. No templates for common docs** | Medium | "I upload invoices daily, give me a 1-click preset" |
| **16. Settings buried in nav** | Low | Alert preferences not easily accessible |
| **17. No mobile-responsive layout** | High | B2C users on phones can't upload easily |
| **18. Logout in every nav** | Low | Accidental logout risk |
| **19. No "Quick Export" button** | Medium | Must navigate to review page first |
| **20. AI summary collapsed by default** | Low | User must click to see insights |

### **🟢 Minor Issues**

| Issue | Impact | User Pain |
|-------|--------|-----------|
| **21. 50MB file size limit** | Low | Most docs under 50MB, but no chunked upload for larger |
| **22. No file history/versioning** | Low | Can't see previous uploads of same file |
| **23. No sharing/collaboration** | Low | Can't share document with team |
| **24. No API key for automation** | Low | Power users want to automate uploads |
| **25. Success messages disappear** | Low | 4-5 second timeout may be too fast |

---

## 6. SIMPLIFICATION SUGGESTIONS FOR B2C

### **Phase 1: Immediate UX Wins (Low Effort, High Impact)**

#### **A. Streamline Upload Flow**
```
BEFORE: Dashboard → Upload Section → Browse → Select → Upload → Wait
AFTER:  Dashboard with prominent drop zone → Drop file → Auto-upload
```
**Changes**:
- Make entire dashboard a drop zone (drag anywhere to upload)
- Auto-upload on file drop (skip "Upload" button)
- Show progress inline in document list

#### **B. One-Click Export**
```
BEFORE: Review page → Export button → Wait for AI → Download button
AFTER:  Document list → Export icon → Instant download
```
**Changes**:
- Add export icon to each document card in list
- Export + download in single action (no AI review for quick export)
- Add "Advanced Export" option for AI review use case

#### **C. Real-Time Status Updates**
```
BEFORE: Upload → Manual refresh to check status
AFTER:  Upload → Live status badge updates via WebSocket
```
**Implementation**:
- Add WebSocket topic: `/ws/documents/:userId`
- Push events: `DocumentProcessing`, `DocumentComplete`, `DocumentFailed`
- Update document list in real-time

#### **D. Inline Document Preview**
```
BEFORE: Click document → Navigate to review page → See data
AFTER:  Hover document card → Tooltip shows key extracted fields
```
**Implementation**:
- Add `data-preview` attribute to document cards
- Show tooltip with: document type, key fields (supplier, total, date)
- "View Full Details" link for review page

### **Phase 2: Modernize UI/UX (Medium Effort)**

#### **E. Simplify Language**
| Before (Technical) | After (Consumer-Friendly) |
|-------------------|---------------------------|
| "Completeness Score: 87%" | "✓ 87% Complete" |
| "Line Items Extracted: 24" | "✓ 24 Items Found" |
| "Parties Found: 3" | "✓ 3 Companies Identified" |
| "Validation Metrics" | "Quality Check" |
| "AI Agent Analysis" | "Smart Insights" |
| "Export with AI Review" | "Enhanced Export" |

#### **F. Mobile-First Redesign**
- Responsive layout (currently desktop-only)
- Mobile upload via camera (take photo of document)
- Simplified mobile navigation (bottom tab bar)
- Swipe gestures (swipe left to delete, swipe right to export)

#### **G. Onboarding Flow**
```
First-time user:
1. "Welcome! Let's convert your first document"
2. Drop zone with sample document option
3. Upload sample → Show results in 5 seconds
4. "Try your own document now"
5. Success → "Share with friends" prompt
```

### **Phase 3: Advanced Features (High Effort)**

#### **H. Smart Templates**
```
User uploads invoice (5 times) → System detects pattern
  → "We noticed you upload invoices often. Save as template?"
  → Next invoice: Auto-extract using saved template (faster)
```

#### **I. Batch Upload**
```
Drop 10 PDFs at once → All upload in parallel
  → Progress: "Processing 10 documents..." (7 complete, 3 in progress)
  → Bulk export: "Download All as ZIP"
```

#### **J. Instant Preview (No Processing Wait)**
```
Upload document → Show thumbnail preview immediately
  → "Processing in background..."
  → Extracted data populates progressively (field by field)
  → No waiting for full extraction before seeing anything
```

#### **K. Keyboard Shortcuts**
- `Ctrl+U` - Upload document
- `Ctrl+E` - Export selected document
- `Ctrl+R` - Refresh document list
- `Esc` - Close modal/cancel operation
- Arrow keys - Navigate document list

#### **L. Document Chat (AI Assistant)**
```
"Where is the invoice total?"
  → AI highlights the field in preview
"Change supplier name to 'Acme Corp'"
  → AI updates extracted data
"Export as Excel"
  → Instant download
```

---

## 7. PROPOSED SIMPLIFIED FLOW (B2C Consumer Version)

### **Ultra-Simplified 3-Step Flow**

#### **Step 1: Upload (No Clicking)**
```
Landing Page:
┌──────────────────────────────────────┐
│  Drop Your Document Here             │
│  📄 Drag & Drop Anywhere             │
│  or click to browse                   │
│                                       │
│  Supported: PDF, Word, Excel, Images │
└──────────────────────────────────────┘
```
- **Action**: User drops file
- **Result**: Instant upload starts, progress shown inline
- **No "Upload" button needed**

#### **Step 2: View Results (Auto-Opens)**
```
Results Page (auto-opens after processing):
┌──────────────────────────────────────┐
│  ✓ Your Document is Ready!           │
│                                       │
│  📋 Invoice #12345                    │
│  💰 Total: $4,520.00                  │
│  🏢 From: Acme Corp                   │
│  📅 Date: Jan 15, 2026                │
│                                       │
│  [💾 Download]  [✏️ Edit]  [🔄 Upload Another] │
└──────────────────────────────────────┘
```
- **Action**: Auto-navigates to results (no manual click)
- **Result**: Key fields shown prominently
- **Download button prominent (primary CTA)**

#### **Step 3: Download (One Click)**
```
Click "Download" →
  → Dropdown appears: JSON | CSV | Excel | PDF
  → Click format
  → Instant download (no AI review by default)
```
- **Action**: Single click
- **Result**: File downloads immediately
- **Optional**: "Enhanced with AI" toggle for advanced users

### **Comparison: Current vs Proposed**

| Current Flow | Steps | Clicks | Proposed Flow | Steps | Clicks |
|--------------|-------|--------|---------------|-------|--------|
| Dashboard → Upload Section | 1 | 1 | Drop file anywhere | 1 | 0 |
| Browse → Select file | 2 | 2 | Auto-upload starts | - | - |
| Click Upload button | 3 | 3 | Results auto-open | 2 | 0 |
| Wait for processing | - | - | Download button shown | 3 | 1 |
| Refresh to check status | 4 | 4 | Select format | 4 | 1 |
| Click document to review | 5 | 5 | File downloads | - | - |
| Review page loads | 6 | - | **Total** | **4** | **2** |
| Click Export | 7 | 6 | | | |
| Wait for AI review | - | - | | | |
| Click Download | 8 | 7 | | | |
| **Total** | **8** | **7** | | | |

**Result**: 75% reduction in steps, 70% reduction in clicks

---

## 8. COMPONENT REFACTORING ROADMAP

### **New Components to Create**

#### **1. DropZoneOverlay.tsx** (Global Drop Zone)
```tsx
// Full-page overlay when dragging files
<DropZoneOverlay onDrop={handleGlobalDrop}>
  <div>Drop Anywhere to Upload</div>
</DropZoneOverlay>
```

#### **2. DocumentCardPreview.tsx** (Hover Preview)
```tsx
// Tooltip-style preview on hover
<DocumentCardPreview document={doc}>
  <div>
    <span>Type: {doc.type}</span>
    <span>Total: {doc.extractedTotal}</span>
    <span>Date: {doc.extractedDate}</span>
  </div>
</DocumentCardPreview>
```

#### **3. QuickExportMenu.tsx** (One-Click Export)
```tsx
// Dropdown menu attached to document card
<QuickExportMenu documentId={doc.id} formats={['json', 'csv', 'pdf']}>
  <button>Export ⬇️</button>
</QuickExportMenu>
```

#### **4. ProgressToast.tsx** (Non-Blocking Progress)
```tsx
// Bottom-right toast showing upload/export progress
<ProgressToast 
  message="Converting invoice.pdf..."
  progress={75}
  onComplete={() => showResults()}
/>
```

#### **5. SmartResultsView.tsx** (Simplified Review)
```tsx
// Stripped-down review page for B2C
<SmartResultsView document={doc}>
  <KeyFields fields={extracted} />
  <PrimaryAction label="Download" onClick={download} />
  <SecondaryAction label="Edit" onClick={edit} />
</SmartResultsView>
```

### **Components to Simplify/Merge**

| Current | Proposed | Reason |
|---------|----------|--------|
| `DocumentUpload.tsx` + `Dashboard.tsx` | Merge into single `UploadDashboard.tsx` | Less navigation, unified experience |
| `DocumentReviewDetail.tsx` | Split into `QuickView.tsx` + `AdvancedReview.tsx` | Separate simple/power user paths |
| `PreferencesPage.tsx` | Reduce tabs from 4 to 2 (Alerts + Display) | Fewer options for consumers |
| `Layout.tsx` | Add mobile bottom nav variant | Mobile-first approach |

---

## SUMMARY SCORECARD

| Dimension | Current Score | Target Score | Priority Actions |
|-----------|---------------|--------------|------------------|
| **Upload Ease** | 6/10 | 9/10 | Add global drop zone, auto-upload |
| **Status Clarity** | 5/10 | 9/10 | Real-time WebSocket updates |
| **Export Speed** | 4/10 | 9/10 | One-click export, skip AI review |
| **Mobile UX** | 2/10 | 8/10 | Responsive design, camera upload |
| **Onboarding** | 3/10 | 8/10 | Interactive tutorial, sample docs |
| **Consumer Language** | 5/10 | 9/10 | Replace technical terms |
| **Performance** | 7/10 | 9/10 | Real progress tracking, lazy loading |
| **Accessibility** | 6/10 | 8/10 | Keyboard shortcuts, ARIA labels |

**Overall: 38/80 (48%) → Target: 69/80 (86%)**

---

## PRIORITY MATRIX (Effort vs Impact)

```
                    HIGH IMPACT
                         ↑
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     │  🟢 DO FIRST     │  🟡 DO NEXT      │
     │                  │                  │
LOW  │  • Global drop   │  • Batch upload  │  HIGH
EFFORT │ zone           │  • Mobile UI     │  EFFORT
     │  • One-click     │  • Document chat │
     │    export        │  • Templates     │
     │  • Real-time     │                  │
     │    status        │                  │
     │  • Simplify      │                  │
     │    language      │                  │
     ├──────────────────┼──────────────────┤
     │                  │                  │
     │  🔵 DO LATER     │  ⚫ SKIP         │
     │                  │                  │
     │  • Keyboard      │  • API keys      │
     │    shortcuts     │  • Collaboration │
     │  • Inline        │  • Versioning    │
     │    preview       │                  │
     └──────────────────┼──────────────────┘
                    LOW IMPACT
```

---

## ACTION ITEMS (30-Day Sprint)

### **Week 1: Quick Wins**
- [ ] Add global drop zone overlay
- [ ] Enable auto-upload on file drop
- [ ] Add real-time status updates via WebSocket
- [ ] Simplify language (8 key terms)

### **Week 2: Export Optimization**
- [ ] Implement one-click export from document list
- [ ] Add export format quick menu
- [ ] Skip AI review for "Quick Export"
- [ ] Show download progress inline

### **Week 3: Mobile & Onboarding**
- [ ] Responsive layout (mobile breakpoints)
- [ ] Bottom navigation for mobile
- [ ] Interactive onboarding flow (4 steps)
- [ ] Sample document for first-time users

### **Week 4: Polish & Testing**
- [ ] A/B test: Current flow vs simplified flow
- [ ] User testing with 10 B2C users
- [ ] Fix top 5 friction points from feedback
- [ ] Deploy to production with feature flag

**Expected Result**: 50% reduction in time-to-download, 30% increase in conversion rate
