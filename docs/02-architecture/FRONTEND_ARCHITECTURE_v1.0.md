# Frontend Architecture Document

**Version:** 1.0  
**Status:** APPROVED  
**Framework:** React 18 + TypeScript 5.3  
**Build Tool:** Vite  
**Last Updated:** 2026-01-17

---

## Frontend Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            React Application (SPA)                      │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │         Page Components                          │  │ │
│  │  │  Login / Dashboard / Detail / Upload / PO View   │  │ │
│  │  └────────┬─────────────────────────────┬───────────┘  │ │
│  │           │                             │              │ │
│  │  ┌────────▼──────────────────────────────▼──────────┐  │ │
│  │  │     Shared UI Components                        │  │ │
│  │  │  Header, Sidebar, Modal, Button, Input          │  │ │
│  │  └────────┬─────────────────────────────┬───────────┘  │ │
│  │           │                             │              │ │
│  │  ┌────────▼──────────────────────────────▼──────────┐  │ │
│  │  │       State Management (React Hooks)            │  │ │
│  │  │  useState, useContext, useReducer               │  │ │
│  │  └────────┬─────────────────────────────┬───────────┘  │ │
│  │           │                             │              │ │
│  │  ┌────────▼──────────────────────────────▼──────────┐  │ │
│  │  │       API Service Layer (useEffect)              │  │ │
│  │  │  API calls, data fetching, error handling        │  │ │
│  │  └────────┬─────────────────────────────┬───────────┘  │ │
│  └──────────────┼───────────────────────────┼──────────────┘ │
└─────────────────┼───────────────────────────┼────────────────┘
                  │                           │
              HTTP REST API
                  │                           │
        ┌─────────▼──────────────┐
        │   Backend (FastAPI)    │
        │   Azure Container Apps │
        └────────────────────────┘
```

---

## Project Structure

```
frontend/
├── index.html                 # Entry HTML file
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies & scripts
├── .env                       # Environment variables
│
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Root component & router
│   │
│   ├── pages/
│   │   ├── Login.tsx         # Login page
│   │   ├── Dashboard.tsx     # Document list view
│   │   ├── DocumentDetail.tsx # Document detail page
│   │   ├── UploadDocument.tsx # Document upload
│   │   ├── Workflow.tsx      # Workflow progress view
│   │   ├── Comparison.tsx    # Quote comparison
│   │   └── POView.tsx        # Purchase order view
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.tsx       # Top navigation
│   │   │   ├── Sidebar.tsx      # Side navigation
│   │   │   ├── Layout.tsx       # Main layout wrapper
│   │   │   └── LoadingSpinner.tsx
│   │   │
│   │   ├── ui/
│   │   │   ├── Button.tsx       # Reusable button
│   │   │   ├── Input.tsx        # Input field
│   │   │   ├── Modal.tsx        # Modal dialog
│   │   │   ├── Card.tsx         # Card component
│   │   │   └── Table.tsx        # Data table
│   │   │
│   │   ├── forms/
│   │   │   ├── LoginForm.tsx       # Login form
│   │   │   ├── DocumentUploadForm.tsx
│   │   │   └── QuotationForm.tsx
│   │   │
│   │   └── document/
│   │       ├── DocumentList.tsx       # Render doc list
│   │       ├── DocumentCard.tsx       # Single doc card
│   │       ├── ExtractedDataView.tsx # Show extracted data
│   │       └── DocumentMetadata.tsx  # Document info
│   │
│   ├── services/
│   │   ├── api.ts           # API client (axios/fetch)
│   │   ├── auth.ts          # Auth service (JWT)
│   │   └── storage.ts       # Local storage helpers
│   │
│   ├── hooks/
│   │   ├── useAuth.ts       # Auth context hook
│   │   ├── useFetch.ts      # Data fetching hook
│   │   ├── useDocument.ts   # Document state hook
│   │   └── useWorkflow.ts   # Workflow state hook
│   │
│   ├── context/
│   │   ├── AuthContext.tsx  # Auth context provider
│   │   └── AppContext.tsx   # App-wide state
│   │
│   ├── types/
│   │   ├── index.ts         # TypeScript types
│   │   ├── api.ts           # API response types
│   │   └── models.ts        # Domain models
│   │
│   ├── utils/
│   │   ├── constants.ts     # App constants
│   │   ├── helpers.ts       # Utility functions
│   │   └── formatters.ts    # Date/number formatting
│   │
│   ├── styles/
│   │   ├── globals.css      # Global styles
│   │   ├── variables.css    # CSS variables
│   │   └── components.css   # Component styles
│   │
│   └── App.tsx              # App component with routing
│
├── dist/                    # Build output (generated)
└── node_modules/            # Dependencies (git ignored)
```

---

## Core Components

### 1. Page Components

#### Login Page
```typescript
// pages/Login.tsx
- Display login form
- Handle form submission
- Validate credentials
- Store JWT token
- Redirect to dashboard
```

#### Dashboard
```typescript
// pages/Dashboard.tsx
- List all user documents
- Display document cards
- Search & filter documents
- Pagination (20 per page)
- Upload button
- Link to detail view
```

#### DocumentDetail
```typescript
// pages/DocumentDetail.tsx
- Display full document info
- Show extracted data
- Allow editing extracted fields
- Workflow progress indicator
- Action buttons (edit, delete, workflow)
```

#### UploadDocument
```typescript
// pages/UploadDocument.tsx
- File drag & drop area
- File type selection
- Upload progress indicator
- Extraction status
- Redirect after completion
```

#### Workflow Progress
```typescript
// pages/Workflow.tsx
- Show workflow steps
- Current step highlight
- Step completion status
- Next action prompt
- Timeline view
```

#### Quote Comparison
```typescript
// pages/Comparison.tsx
- Display multiple quotations
- Side-by-side comparison table
- Scoring breakdown
- Best option highlighted
- Select best button
```

#### Purchase Order View
```typescript
// pages/POView.tsx
- Display generated PO
- Edit PO details
- Preview before send
- Send to vendor button
- Download/print options
```

### 2. Shared Components

#### UI Components (`components/ui/`)
```typescript
<Button 
  variant="primary|secondary|danger"
  size="sm|md|lg"
  loading={isLoading}
/>

<Input 
  type="text|email|number|date"
  value={value}
  onChange={handleChange}
  error={errorMessage}
/>

<Modal 
  isOpen={true}
  title="Confirm Action"
  onClose={handleClose}
>
  {/* Modal content */}
</Modal>

<Card className="p-4">
  {/* Card content */}
</Card>

<Table 
  columns={[...]}
  data={[...]}
  onRowClick={handleRowClick}
/>
```

#### Layout Components
```typescript
<Layout>
  <Header /> {/* Top navigation */}
  <Sidebar /> {/* Side navigation */}
  <main className="main-content">
    {/* Page content */}
  </main>
</Layout>
```

### 3. State Management

**Pattern:** React Hooks + Context API (no external store needed)

```typescript
// hooks/useAuth.ts
const { user, isLoggedIn, login, logout } = useAuth();

// hooks/useFetch.ts
const { data, loading, error } = useFetch(
  '/api/v1/documents',
  { skip: 0, limit: 20 }
);

// hooks/useDocument.ts
const { documents, selectedDoc, selectDocument } = useDocument();

// context/AuthContext.tsx
const AuthContext = createContext();
<AuthProvider>
  {/* App components */}
</AuthProvider>
```

### 4. API Service Layer

```typescript
// services/api.ts
class APIClient {
  private baseURL = import.meta.env.VITE_API_URL;
  private token: string | null = null;

  async request(
    method: 'GET'|'POST'|'PATCH'|'DELETE',
    endpoint: string,
    data?: any
  ) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: data ? JSON.stringify(data) : undefined
    });

    if (response.status === 401) {
      // Token expired, redirect to login
      this.logout();
    }

    return response.json();
  }

  // Methods
  login(email: string, password: string) { }
  getDocuments(page: number) { }
  getDocument(id: string) { }
  uploadDocument(file: File) { }
  updateDocument(id: string, data: any) { }
  deleteDocument(id: string) { }
  createWorkflow(documentId: string) { }
}

export const api = new APIClient();
```

---

## Data Flow: Loading Documents

```
1. User navigates to Dashboard
   ├─ Dashboard component mounts
   ├─ useEffect trigger
   └─ useFetch('/api/v1/documents') called
   
2. API call to backend
   ├─ GET /api/v1/documents sent with JWT
   ├─ Backend validates token
   ├─ Returns document list
   └─ Response received by frontend
   
3. Update component state
   ├─ Documents stored in state
   ├─ Loading state set to false
   └─ Render document list
   
4. User interaction
   ├─ Click on document
   ├─ DocumentDetail page loads
   ├─ GET /api/v1/documents/{id} called
   └─ Show full document details
```

---

## Data Flow: Upload & Extract

```
1. User selects file on UploadDocument page
   ├─ File validation (size, type)
   ├─ Display file info
   └─ Show upload button
   
2. User clicks upload
   ├─ POST /api/v1/documents/upload
   ├─ Multipart form data sent
   ├─ Show progress indicator
   └─ File uploaded to backend
   
3. Backend processes
   ├─ Stored in Blob Storage
   ├─ Sent to Azure Document Intelligence
   ├─ Extraction completed
   └─ Results stored in Cosmos DB
   
4. Poll for extraction status
   ├─ Frontend polls GET /api/v1/documents/{id}
   ├─ Check extraction_status
   ├─ When complete, redirect
   └─ Show extracted data
```

---

## Component Props & TypeScript Types

```typescript
// types/models.ts
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'officer' | 'approver' | 'admin';
}

export interface Document {
  document_id: string;
  filename: string;
  document_type: string;
  status: 'uploading' | 'extracting' | 'extracted' | 'archived';
  extracted_confidence: number;
  uploaded_at: string;
}

export interface ExtractedData {
  project_name: string;
  budget: number;
  required_by: string;
  line_items: LineItem[];
}

export interface Workflow {
  workflow_id: string;
  document_id: string;
  current_step: number;
  total_steps: number;
  steps: WorkflowStep[];
}

export interface DocumentCardProps {
  document: Document;
  onSelect: (id: string) => void;
  isSelected: boolean;
}
```

---

## Routing Configuration

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/documents" />} />
          <Route path="/documents" element={<Dashboard />} />
          <Route path="/documents/:id" element={<DocumentDetail />} />
          <Route path="/upload" element={<UploadDocument />} />
          <Route path="/workflow/:id" element={<Workflow />} />
          <Route path="/comparison/:id" element={<Comparison />} />
          <Route path="/po/:id" element={<POView />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Build & Deployment

**Development Server:**
```bash
npm run dev
# Starts Vite dev server on http://localhost:5173
# Hot module replacement enabled
```

**Production Build:**
```bash
npm run build
# Output: dist/ folder
# Files optimized and minified
# Ready for deployment to Azure Static Web App
```

**Environment Configuration:**
```
# .env (development)
VITE_API_URL=http://localhost:8000

# .env.production (production)
VITE_API_URL=https://api.kraftdintel.com
```

---

## Performance & Optimization

| Strategy | Implementation |
|----------|-----------------|
| Code splitting | Route-based lazy loading |
| Image optimization | Compress images, use WebP |
| Caching | HTTP cache headers |
| Minification | Vite build minifies all code |
| Tree shaking | Remove unused imports |
| Bundle analysis | Monitor bundle size |
| Pagination | 20 items per page |
| Memoization | React.memo for expensive components |

---

## Error Handling

```typescript
// hooks/useFetch.ts
try {
  const response = await api.request(method, endpoint);
  if (!response.ok) {
    throw new APIError(response.status, response.data);
  }
  setData(response.data);
} catch (error) {
  setError(error.message);
  // Show error toast to user
}
```

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

**Reference:** `/docs/02-architecture/FRONTEND_ARCHITECTURE_v1.0.md`
