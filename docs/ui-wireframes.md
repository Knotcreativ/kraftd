# Kraftd Docs — Frontend UI Wireframes & Component Architecture

**Version**: 1.0  
**Framework**: React 18.3 + TypeScript 5.9 + Vite 5.0  
**State Management**: React Context + Custom Hooks  
**Styling**: Tailwind CSS  
**UI Library**: Headless UI components  

This document defines the **complete frontend user experience** for document intelligence processing.

The UI is built around a **prompt-first, document-intelligence workflow** — minimal friction, intuitive progression through 7 processing stages, and clear human-in-the-loop control.

---

# Frontend Architecture

```
Dashboard Home
    ↓
Upload & Prompt Entry
    ↓
Processing (auto: classify → extract → infer → validate)
    ↓
AI Summary + Schema Preview
    ↓
Schema Editor (optional user edits)
    ↓
Output Type Selection
    ↓
Conversion Result (download)
    ↓
Feedback Collection
    ↓
Reset → New Conversion
```

---

# Page 1: Dashboard Home

## Purpose
Landing page after login. Entry point for document conversions.

## Wireframe

```
┌─────────────────────────────────────────────┐
│  Kraftd    Settings    Profile    Logout    │  ← NavigationBar
├─────────────────────────────────────────────┤
│                                             │
│  Welcome back, John!                        │
│                                             │
│  Quota: 487 / 5000 documents used ▓▓░░░░   │  ← QuotaIndicator
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  + Start New Conversion              │   │  ← Action Button
│  └─────────────────────────────────────┘   │
│                                             │
│  Recent Conversions                         │
│  ┌─────────────────────────────────────┐   │
│  │ 📄 quotation.pdf                    │   │
│  │ QUOTATION extracted 2 hours ago     │   │
│  │ [View] [Download] [Re-process]      │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ 📄 invoice.pdf                      │   │
│  │ INVOICE extracted 5 hours ago       │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

## Components

### NavigationBar
```typescript
interface NavigationBarProps {
  userEmail: string
  onLogout: () => void
  onSettings: () => void
}

const NavigationBar: React.FC<NavigationBarProps> = ({
  userEmail,
  onLogout,
  onSettings
}) => (
  <nav className="flex justify-between items-center p-4 bg-white border-b">
    <div className="text-2xl font-bold">Kraftd</div>
    <div className="flex gap-4">
      <button onClick={onSettings}>Settings</button>
      <span>{userEmail}</span>
      <button onClick={onLogout}>Logout</button>
    </div>
  </nav>
)
```

### QuotaIndicator
```typescript
interface QuotaIndicatorProps {
  used: number
  limit: number
}

const QuotaIndicator: React.FC<QuotaIndicatorProps> = ({ used, limit }) => {
  const percentage = (used / limit) * 100
  return (
    <div className="p-4 bg-blue-50 rounded-lg">
      <p className="text-sm font-semibold">
        Documents: {used} / {limit}
      </p>
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div
          className="bg-blue-500 h-2 rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
```

---

# Page 2: Upload & Prompt

## Purpose
Core workflow entry. User uploads documents and describes intent.

## Wireframe

```
┌────────────────────────────────────────────────┐
│  Kraftd                           Settings     │
├────────────────────────────────────────────────┤
│                                                │
│  New Conversion                                │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  Drop files here or click to upload      │ │
│  │  (PDF, DOCX, XLSX, images • max 50 MB)  │ │
│  │                                          │ │
│  │           [Choose Files]                 │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Uploaded Files:                               │
│  [📄 quotation.pdf ✕] [📄 invoice.pdf ✕]     │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ What do you want to do with these docs?  │ │
│  │                                          │ │
│  │ (e.g., "Extract costs", "Summarize",    │ │
│  │  "Compare suppliers", "Create PO")      │ │
│  │                                          │ │
│  │ ┌──────────────────────────────────────┐│ │
│  │ │                                      ││ │
│  │ │                                      ││ │
│  │ │                                      ││ │
│  │ └──────────────────────────────────────┘│ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Quick Actions:                                │
│  [Extract Text] [Extract Tables]              │
│  [Summarize] [Rebuild Structure]              │
│                                                │
│                    [Continue →] (enabled)     │
│                                                │
└────────────────────────────────────────────────┘
```

## Components

### FileUploader
```typescript
interface FileUploaderProps {
  onFilesSelected: (files: File[]) => void
  maxFiles?: number
  maxSizeBytes?: number
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onFilesSelected,
  maxFiles = 10,
  maxSizeBytes = 50 * 1024 * 1024
}) => {
  const [isDragActive, setIsDragActive] = React.useState(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length <= maxFiles) {
      onFilesSelected(files)
    } else {
      alert(`Max ${maxFiles} files allowed`)
    }
  }

  return (
    <div
      onDragEnter={() => setIsDragActive(true)}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}`}
    >
      <p className="text-gray-600 mb-2">Drop files here or click to upload</p>
      <p className="text-sm text-gray-500">PDF, DOCX, XLSX, images • max 50 MB</p>
      <input
        type="file"
        multiple
        hidden
        onChange={(e) => e.target.files && onFilesSelected(Array.from(e.target.files))}
      />
      <button className="mt-4 px-4 py-2 bg-blue-500 text-white rounded">
        Choose Files
      </button>
    </div>
  )
}
```

### FileChip
```typescript
interface FileChipProps {
  filename: string
  fileType: string
  onRemove: () => void
}

const FileChip: React.FC<FileChipProps> = ({ filename, fileType, onRemove }) => (
  <div className="inline-flex items-center gap-2 px-3 py-2 bg-blue-100 text-blue-800 rounded-full">
    <span className="text-sm font-medium">{filename}</span>
    <button onClick={onRemove} className="hover:bg-blue-200 rounded-full p-1">
      ✕
    </button>
  </div>
)
```

### PromptBox
```typescript
interface PromptBoxProps {
  value: string
  onChange: (text: string) => void
  onQuickAction: (action: string) => void
}

const PromptBox: React.FC<PromptBoxProps> = ({ value, onChange, onQuickAction }) => (
  <div className="space-y-4">
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="What do you want to do with these documents? (e.g., 'Extract costs', 'Compare suppliers', 'Summarize')"
      className="w-full h-24 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500"
    />
    <div className="flex gap-2">
      <button
        onClick={() => onQuickAction("Extract Text")}
        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
      >
        Extract Text
      </button>
      <button
        onClick={() => onQuickAction("Extract Tables")}
        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
      >
        Extract Tables
      </button>
      <button
        onClick={() => onQuickAction("Summarize")}
        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
      >
        Summarize
      </button>
      <button
        onClick={() => onQuickAction("Rebuild Structure")}
        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
      >
        Rebuild Structure
      </button>
    </div>
  </div>
)
```

---

# Page 3: Processing (Automatic)

## Purpose
Shows real-time processing progress through all stages.

## Wireframe

```
┌────────────────────────────────────────────┐
│  Kraftd                           Settings  │
├────────────────────────────────────────────┤
│                                            │
│  Processing Documents...                   │
│                                            │
│  ✓ Upload                    100%          │
│  ✓ Classify Document Type    100%          │
│  ⏳ Extract Fields           45%  ▓▓░░░░  │
│    Detect parties, dates, line items...    │
│  ○ Infer Business Logic      0%            │
│  ○ Validate Quality          0%            │
│  ○ Transform Data            0%            │
│  ○ Export                    0%            │
│                                            │
│  Estimated time: 2-4 seconds               │
│                                            │
│              [Cancel]                      │
│                                            │
└────────────────────────────────────────────┘
```

## Component

### ProcessingOverlay
```typescript
interface ProcessingStage {
  name: string
  status: 'pending' | 'in-progress' | 'complete' | 'error'
  progress: number // 0-100
  description?: string
}

interface ProcessingOverlayProps {
  stages: ProcessingStage[]
  onCancel: () => void
}

const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({
  stages,
  onCancel
}) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
    <div className="bg-white rounded-lg p-8 max-w-md w-full">
      <h2 className="text-xl font-bold mb-6">Processing Documents...</h2>
      
      <div className="space-y-4 mb-6">
        {stages.map((stage, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-medium">{stage.name}</span>
              <span className="text-sm text-gray-500">{stage.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300
                  ${stage.status === 'complete' ? 'bg-green-500' : 
                    stage.status === 'in-progress' ? 'bg-blue-500' : 
                    'bg-gray-300'}`}
                style={{ width: `${stage.progress}%` }}
              />
            </div>
            {stage.description && (
              <p className="text-xs text-gray-500">{stage.description}</p>
            )}
          </div>
        ))}
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Estimated time: 2-4 seconds
      </p>
      
      <button
        onClick={onCancel}
        className="w-full px-4 py-2 border rounded hover:bg-gray-50"
      >
        Cancel
      </button>
    </div>
  </div>
)
```

---

# Page 4: AI Summary + Schema Preview

## Purpose
Show what the AI understood about the document.

## Wireframe

```
┌─────────────────────────────────────────────┐
│  Kraftd                         Settings    │
├─────────────────────────────────────────────┤
│                                             │
│  Summary & Preview                          │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ 🤖 AI Summary                        │  │
│  ├──────────────────────────────────────┤  │
│  │ This is a quotation from Tech        │  │
│  │ Solutions Inc for IT development     │  │
│  │ services. Includes 180 hours of      │  │
│  │ work (100 hrs frontend, 80 hrs       │  │
│  │ backend) at USD 150-175/hr with      │  │
│  │ 30-day validity and Net 30 payment.  │  │
│  │                                      │  │
│  │ Key Findings:                        │  │
│  │ • Supplier: Tech Solutions Inc       │  │
│  │ • Total Cost: USD 29,000             │  │
│  │ • Delivery: 8 weeks                  │  │
│  │ • Confidence: 94%                    │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ Extracted Data (Preview)             │  │
│  ├──────────────────────────────────────┤  │
│  │ Document Type: QUOTATION             │  │
│  │ Supplier: Tech Solutions Inc         │  │
│  │ Valid Until: Feb 20, 2026            │  │
│  │ Total Cost: USD 29,000               │  │
│  │ Tax (5%): USD 1,450                  │  │
│  │ Delivery: 8 weeks                    │  │
│  │ Payment Terms: Net 30                │  │
│  │                                      │  │
│  │ Line Items: (2 items)                │  │
│  │ • Frontend Development - 100 hrs     │  │
│  │ • Backend API - 80 hrs               │  │
│  │                                      │  │
│  │ ⚠ Warning: Warranty period missing   │  │
│  │ ℹ Confidence: High (94%)             │  │
│  └──────────────────────────────────────┘  │
│                                             │
│           [Edit Data] [Continue →]         │
│                                             │
└─────────────────────────────────────────────┘
```

## Components

### SummaryCard
```typescript
interface SummaryCardProps {
  text: string
  keyFindings: Array<{ label: string; value: string }>
  confidence: number
}

const SummaryCard: React.FC<SummaryCardProps> = ({
  text,
  keyFindings,
  confidence
}) => (
  <div className="p-6 border rounded-lg bg-blue-50">
    <h3 className="font-bold flex items-center gap-2 mb-4">
      🤖 AI Summary
    </h3>
    <p className="text-gray-700 leading-relaxed mb-4">{text}</p>
    
    <div className="bg-white rounded p-4 space-y-2">
      <p className="font-semibold text-sm">Key Findings:</p>
      {keyFindings.map((finding, idx) => (
        <div key={idx} className="flex justify-between text-sm">
          <span className="text-gray-600">• {finding.label}</span>
          <span className="font-medium">{finding.value}</span>
        </div>
      ))}
      <div className="pt-2 border-t text-sm">
        Confidence: <span className="font-bold">{confidence}%</span>
      </div>
    </div>
  </div>
)
```

### SchemaPreview
```typescript
interface SchemaField {
  name: string
  value: string | number | null
  status: 'ok' | 'missing' | 'low-confidence' | 'conflict'
  confidence?: number
}

interface SchemaPreviewProps {
  fields: SchemaField[]
  lineItems?: Array<Record<string, any>>
  warnings?: string[]
  onEdit: () => void
}

const SchemaPreview: React.FC<SchemaPreviewProps> = ({
  fields,
  lineItems,
  warnings,
  onEdit
}) => (
  <div className="p-6 border rounded-lg">
    <h3 className="font-bold mb-4">Extracted Data (Preview)</h3>
    
    <div className="space-y-3 mb-6">
      {fields.map((field, idx) => (
        <div key={idx} className="flex justify-between items-center py-2 border-b">
          <span className="text-gray-600">{field.name}</span>
          <div className="flex items-center gap-2">
            <span className="font-medium">
              {field.value ?? <span className="text-gray-400">—</span>}
            </span>
            {field.status === 'missing' && (
              <span className="text-yellow-600 text-sm">⚠ Missing</span>
            )}
            {field.status === 'low-confidence' && (
              <span className="text-orange-600 text-sm">⚠ {field.confidence}%</span>
            )}
          </div>
        </div>
      ))}
    </div>

    {lineItems && lineItems.length > 0 && (
      <div className="mb-6">
        <p className="font-semibold text-sm mb-3">
          Line Items: ({lineItems.length} items)
        </p>
        <ul className="space-y-2 text-sm">
          {lineItems.slice(0, 5).map((item, idx) => (
            <li key={idx} className="text-gray-600">
              • {item.description} - {item.quantity} {item.unit_of_measure}
            </li>
          ))}
          {lineItems.length > 5 && (
            <li className="text-gray-500">+ {lineItems.length - 5} more items</li>
          )}
        </ul>
      </div>
    )}

    {warnings && warnings.length > 0 && (
      <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded">
        {warnings.map((warning, idx) => (
          <p key={idx} className="text-sm text-yellow-800">
            ⚠ {warning}
          </p>
        ))}
      </div>
    )}

    <div className="flex gap-3">
      <button
        onClick={onEdit}
        className="px-4 py-2 border rounded hover:bg-gray-50"
      >
        Edit Data
      </button>
      <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        Continue →
      </button>
    </div>
  </div>
)
```

---

# Page 5: Schema Editor

## Purpose
Allow user to review and edit extracted data before export.

## Wireframe

```
┌─────────────────────────────────────────────────┐
│  Kraftd                           Settings      │
├─────────────────────────────────────────────────┤
│                                                 │
│  Edit Extraction Data                           │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Document Information                     │  │
│  ├──────────────────────────────────────────┤  │
│  │ Document Type  │ QUOTATION              │  │
│  │ Number         │ QUOT-2026-001          │  │
│  │ Issue Date     │ 2026-01-20             │  │
│  │ Validity Until │ 2026-02-20             │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Supplier Information                     │  │
│  ├──────────────────────────────────────────┤  │
│  │ Company       │ Tech Solutions Inc      │  │
│  │ Contact       │ John Smith              │  │
│  │ Email         │ john@tech.com           │  │
│  │ Address       │ 123 Tech Park, SF...    │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Line Items                               │  │
│  ├──────────────────────────────────────────┤  │
│  │ # │ Description │ Qty │ UOM │ Price     │  │
│  ├──────────────────────────────────────────┤  │
│  │ 1 │ Frontend Dev│ 100 │ HR  │ 150.00    │  │
│  │ 2 │ Backend API │ 80  │ HR  │ 175.00    │  │
│  ├──────────────────────────────────────────┤  │
│  │ [+ Add Item]                             │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Totals                                   │  │
│  ├──────────────────────────────────────────┤  │
│  │ Subtotal      │ USD 29,000             │  │
│  │ Tax (5%)      │ USD 1,450              │  │
│  │ Total         │ USD 30,450             │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│                  [Cancel] [Finalize →]         │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Component

### SchemaTableEditor
```typescript
interface EditableField {
  name: string
  value: string | number
  editable: boolean
  onChange: (newValue: string | number) => void
}

interface SchemaTableEditorProps {
  sections: {
    title: string
    fields: EditableField[]
  }[]
  onLineItemAdd: () => void
  onLineItemDelete: (idx: number) => void
  onLineItemChange: (idx: number, field: string, value: any) => void
  lineItems: Array<Record<string, any>>
  onSave: () => void
  onCancel: () => void
}

const SchemaTableEditor: React.FC<SchemaTableEditorProps> = ({
  sections,
  onLineItemAdd,
  lineItems,
  onSave,
  onCancel
}) => (
  <div className="space-y-6">
    {sections.map((section, idx) => (
      <div key={idx} className="p-6 border rounded-lg">
        <h3 className="font-bold mb-4">{section.title}</h3>
        <table className="w-full">
          <tbody>
            {section.fields.map((field, fIdx) => (
              <tr key={fIdx} className="border-b">
                <td className="py-2 text-gray-600 pr-4 w-1/3">{field.name}</td>
                <td className="py-2">
                  {field.editable ? (
                    <input
                      type="text"
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value)}
                      className="border rounded px-3 py-1 w-full"
                    />
                  ) : (
                    <span>{field.value}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ))}

    <div className="p-6 border rounded-lg">
      <h3 className="font-bold mb-4">Line Items</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2">#</th>
            <th className="text-left py-2">Description</th>
            <th className="text-right py-2">Qty</th>
            <th className="text-right py-2">UOM</th>
            <th className="text-right py-2">Price</th>
            <th className="text-center py-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {lineItems.map((item, idx) => (
            <tr key={idx} className="border-b">
              <td className="py-2">{idx + 1}</td>
              <td className="py-2">{item.description}</td>
              <td className="text-right py-2">{item.quantity}</td>
              <td className="text-right py-2">{item.unit_of_measure}</td>
              <td className="text-right py-2">{item.unit_price}</td>
              <td className="text-center py-2">
                <button className="text-red-500 hover:text-red-700">✕</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        onClick={onLineItemAdd}
        className="mt-4 px-3 py-1 text-blue-500 border border-blue-500 rounded hover:bg-blue-50"
      >
        + Add Item
      </button>
    </div>

    <div className="flex gap-3 justify-end">
      <button
        onClick={onCancel}
        className="px-4 py-2 border rounded hover:bg-gray-50"
      >
        Cancel
      </button>
      <button
        onClick={onSave}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Finalize →
      </button>
    </div>
  </div>
)
```

---

# Page 6: Output Type Selection

## Purpose
User selects final export format.

## Wireframe

```
┌──────────────────────────────────────────────┐
│  Kraftd                        Settings      │
├──────────────────────────────────────────────┤
│                                              │
│  Choose Output Format                        │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   📄         │  │   📋         │         │
│  │   WORD       │  │   PDF        │         │
│  │ (.docx)      │  │ (.pdf)       │         │
│  │              │  │              │         │
│  │ Fast & editable  Professional  │         │
│  └──────────────┘  └──────────────┘         │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   📊         │  │   🗂️          │         │
│  │   EXCEL      │  │   JSON       │         │
│  │ (.xlsx)      │  │ (.json)      │         │
│  │              │  │              │         │
│  │ Spreadsheet  │  │ Data import  │         │
│  └──────────────┘  └──────────────┘         │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   📈         │  │   ✍️          │         │
│  │   CSV        │  │   MARKDOWN   │         │
│  │ (.csv)       │  │ (.md)        │         │
│  │              │  │              │         │
│  │ Simple table │  │ Documentation│         │
│  └──────────────┘  └──────────────┘         │
│                                              │
│                       [Convert →]           │
│                                              │
└──────────────────────────────────────────────┘
```

## Component

### OutputTypeSelector
```typescript
interface OutputFormat {
  id: string
  name: string
  ext: string
  icon: string
  description: string
  processing_time_ms: number
}

interface OutputTypeSelectorProps {
  formats: OutputFormat[]
  selectedFormat: string | null
  onSelect: (format: string) => void
  onConvert: () => void
  isConverting: boolean
}

const OutputTypeSelector: React.FC<OutputTypeSelectorProps> = ({
  formats,
  selectedFormat,
  onSelect,
  onConvert,
  isConverting
}) => (
  <div className="space-y-6">
    <h2 className="text-xl font-bold">Choose Output Format</h2>
    
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {formats.map((format) => (
        <button
          key={format.id}
          onClick={() => onSelect(format.id)}
          className={`p-4 rounded-lg border-2 text-center transition-all
            ${selectedFormat === format.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'}`}
        >
          <div className="text-4xl mb-2">{format.icon}</div>
          <div className="font-bold text-sm">{format.name}</div>
          <div className="text-xs text-gray-500">({format.ext})</div>
          <div className="text-xs text-gray-600 mt-2">{format.description}</div>
          <div className="text-xs text-gray-500 mt-1">
            ~{format.processing_time_ms / 1000}s
          </div>
        </button>
      ))}
    </div>

    <div className="flex justify-end">
      <button
        onClick={onConvert}
        disabled={!selectedFormat || isConverting}
        className={`px-6 py-2 rounded text-white font-medium
          ${selectedFormat && !isConverting
            ? 'bg-blue-500 hover:bg-blue-600'
            : 'bg-gray-400 cursor-not-allowed'}`}
      >
        {isConverting ? 'Converting...' : 'Convert →'}
      </button>
    </div>
  </div>
)
```

---

# Page 7: Conversion Result

## Purpose
Display final output and download link.

## Wireframe

```
┌──────────────────────────────────────────┐
│  Kraftd                      Settings    │
├──────────────────────────────────────────┤
│                                          │
│  ✓ Conversion Complete!                  │
│                                          │
│  ┌──────────────────────────────────────┐│
│  │ 📄 quotation-2026-01-22.json         ││
│  ├──────────────────────────────────────┤│
│  │ Size: 45.6 KB                        ││
│  │ Created: 2026-01-22 10:36:00 UTC     ││
│  │ Format: JSON                         ││
│  │ Expires: 2026-01-29 (7 days)         ││
│  │                                      ││
│  │  [⬇ Download]  [Copy Link]          ││
│  └──────────────────────────────────────┘│
│                                          │
│  ┌──────────────────────────────────────┐│
│  │ Other Formats:                       ││
│  │ [📋 PDF]  [🗂️ CSV]  [📊 Excel]      ││
│  └──────────────────────────────────────┘│
│                                          │
│           [Start New Conversion]         │
│                                          │
└──────────────────────────────────────────┘
```

## Component

### OutputCard
```typescript
interface OutputCardProps {
  filename: string
  fileSize: number
  format: string
  createdAt: string
  expiresAt: string
  downloadUrl: string
  onDownload: () => void
  onStartNew: () => void
  otherFormats?: Array<{ format: string; icon: string; available: boolean }>
}

const OutputCard: React.FC<OutputCardProps> = ({
  filename,
  fileSize,
  format,
  createdAt,
  expiresAt,
  downloadUrl,
  onDownload,
  onStartNew,
  otherFormats
}) => (
  <div className="space-y-6 max-w-md mx-auto">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-green-600 mb-2">
        ✓ Conversion Complete!
      </h2>
      <p className="text-gray-600">Your file is ready to download</p>
    </div>

    <div className="p-6 border-2 border-green-200 rounded-lg bg-green-50">
      <div className="flex items-center gap-4 mb-4">
        <div className="text-4xl">📄</div>
        <div>
          <p className="font-bold">{filename}</p>
          <p className="text-sm text-gray-600">{format.toUpperCase()}</p>
        </div>
      </div>
      
      <div className="space-y-2 mb-4 text-sm text-gray-600">
        <p>Size: {(fileSize / 1024).toFixed(1)} KB</p>
        <p>Created: {new Date(createdAt).toLocaleString()}</p>
        <p>Expires: {new Date(expiresAt).toLocaleDateString()} (7 days)</p>
      </div>

      <div className="flex gap-2">
        <a
          href={downloadUrl}
          onClick={onDownload}
          className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-center text-sm font-medium"
        >
          ⬇ Download
        </a>
        <button className="px-4 py-2 border rounded hover:bg-gray-50 text-sm">
          Copy Link
        </button>
      </div>
    </div>

    {otherFormats && otherFormats.length > 0 && (
      <div className="p-4 border rounded-lg">
        <p className="text-sm font-semibold mb-3">Generate Other Formats:</p>
        <div className="flex gap-2 flex-wrap">
          {otherFormats.map((fmt) => (
            <button
              key={fmt.format}
              disabled={!fmt.available}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
            >
              {fmt.icon} {fmt.format.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    )}

    <button
      onClick={onStartNew}
      className="w-full px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium"
    >
      Start New Conversion
    </button>
  </div>
)
```

---

# Page 8: Feedback Modal

## Purpose
Collect user feedback after download (improves AI model).

## Wireframe

```
┌─────────────────────────────────────┐
│  How was your experience?           │
├─────────────────────────────────────┤
│                                     │
│  Quality of extraction:  ⭐⭐⭐⭐⭐   │
│  Accuracy:               ⭐⭐⭐⭐    │
│  Completeness:           ⭐⭐⭐⭐⭐   │
│                                     │
│  Any comments?                      │
│  ┌─────────────────────────────────┐│
│  │ Excellent work! The extraction  ││
│  │ was very accurate and complete. ││
│  │ Only minor issue with warranty. ││
│  └─────────────────────────────────┘│
│                                     │
│     [Submit] [Skip]                 │
│                                     │
└─────────────────────────────────────┘
```

## Component

### FeedbackModal
```typescript
interface FeedbackData {
  qualityRating: number
  accuracyRating: number
  completenessRating: number
  comments: string
  feedbackType: 'positive' | 'negative' | 'neutral' | 'suggestion'
}

interface FeedbackModalProps {
  isOpen: boolean
  onSubmit: (data: FeedbackData) => void
  onSkip: () => void
  isSubmitting: boolean
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onSubmit,
  onSkip,
  isSubmitting
}) => {
  const [feedback, setFeedback] = React.useState<FeedbackData>({
    qualityRating: 0,
    accuracyRating: 0,
    completenessRating: 0,
    comments: '',
    feedbackType: 'positive'
  })

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">How was your experience?</h2>

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">Quality of extraction</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  onClick={() => setFeedback({ ...feedback, qualityRating: rating })}
                  className={`text-2xl transition-transform hover:scale-125
                    ${rating <= feedback.qualityRating ? 'opacity-100' : 'opacity-30'}`}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Accuracy</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  onClick={() => setFeedback({ ...feedback, accuracyRating: rating })}
                  className={`text-2xl transition-transform hover:scale-125
                    ${rating <= feedback.accuracyRating ? 'opacity-100' : 'opacity-30'}`}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Completeness</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  onClick={() => setFeedback({ ...feedback, completenessRating: rating })}
                  className={`text-2xl transition-transform hover:scale-125
                    ${rating <= feedback.completenessRating ? 'opacity-100' : 'opacity-30'}`}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Comments (optional)</label>
            <textarea
              value={feedback.comments}
              onChange={(e) => setFeedback({ ...feedback, comments: e.target.value })}
              placeholder="Tell us what you think..."
              className="w-full h-24 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onSkip}
            className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
            disabled={isSubmitting}
          >
            Skip
          </button>
          <button
            onClick={() => onSubmit(feedback)}
            disabled={isSubmitting || !feedback.qualityRating}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

---

# State Management

## Context Structure

```typescript
interface ConversionContext {
  // Document state
  conversionId: string | null
  uploadedFiles: File[]
  prompt: string

  // Processing state
  isProcessing: boolean
  processingStages: ProcessingStage[]

  // Extracted data
  extractedDocument: KraftdDocument | null
  aiSummary: string | null
  validationScore: number

  // User edits
  userModifications: UserModification[]
  finalDocument: KraftdDocument | null

  // Output state
  selectedOutputFormat: string | null
  outputUrl: string | null

  // Actions
  setFiles: (files: File[]) => void
  setPrompt: (text: string) => void
  startExtraction: () => Promise<void>
  editDocument: (changes: Partial<KraftdDocument>) => void
  generateOutput: (format: string) => Promise<void>
  submitFeedback: (feedback: FeedbackData) => Promise<void>
  reset: () => void
}

const ConversionProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [state, dispatch] = React.useReducer(conversionReducer, initialState)

  return (
    <ConversionContext.Provider value={state}>
      {children}
    </ConversionContext.Provider>
  )
}
```

---

# Frontend → Backend API Mapping

| Frontend Step | HTTP Method | Endpoint | Response |
|---------------|-------------|----------|----------|
| Login | POST | `/api/v1/auth/login` | access_token |
| Logout | GET | `/api/v1/auth/profile` → logout | — |
| Upload documents | POST | `/api/v1/docs/upload` | document_id, blob_url |
| Upload batch | POST | `/api/v1/docs/upload/batch` | batch_id, documents[] |
| Extract (classify→map→infer→validate) | POST | `/api/v1/docs/extract` | extracted_document, validation_score |
| Get document status | GET | `/api/v1/documents/{id}/status` | status, progress_percent |
| Convert to format | POST | `/api/v1/docs/convert` | output_id, file_url |
| Get outputs | GET | `/api/v1/documents/{id}/output` | outputs[] |
| Submit feedback | POST | `/api/v1/exports/{id}/feedback` | feedback_id |
| Get quota | GET | `/api/v1/auth/profile` | quota_used, quota_limit |

---

# Responsive Design

## Mobile (< 768px)
- Single-column layout
- Full-width buttons
- Stacked cards
- Touch-friendly (48px minimum tap targets)

## Tablet (768px - 1024px)
- Two-column grids
- Horizontal layout for outputs
- Side navigation

## Desktop (> 1024px)
- Full sidebar navigation
- Multi-column grids
- Optimized whitespace

---

# Accessibility

- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader support (semantic HTML, aria labels)
- ✅ Color contrast (4.5:1 for text)
- ✅ Focus indicators
- ✅ Error messages linked to form fields

---

# Performance Targets

- **Page Load**: < 2 seconds
- **Interaction Response**: < 100ms
- **Extract (backend)**: < 5 seconds
- **Export (backend)**: < 3 seconds

---

**Last Updated**: January 22, 2026  
**React Version**: 18.3  
**TypeScript Version**: 5.9  
**Vite Version**: 5.0