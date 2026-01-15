# Azure Document Intelligence Integration Guide

## Overview

The Kraftd Docs MVP backend now supports **Azure Document Intelligence** for intelligent document extraction. When configured, the system will use Azure's pre-trained models for higher accuracy on procurement documents.

## Architecture

- **Primary Extraction**: Azure Document Intelligence (when configured)
- **Fallback**: Local pattern-based extraction (always available)
- **Intelligent Routing**: Auto-detection of Azure credentials; graceful fallback if unavailable

## Setup Instructions

### 1. Create an Azure Document Intelligence Resource

```powershell
# Using Azure CLI
az cognitiveservices account create \
  --name kraftd-doc-intelligence \
  --resource-group <your-rg> \
  --kind DocumentIntelligence \
  --sku standard \
  --location eastus
```

Or create via [Azure Portal](https://portal.azure.com):
- Search for "Document Intelligence"
- Create new resource
- Copy your Endpoint and API Key

### 2. Configure Environment Variables

Set these environment variables in your `.env` file or system environment:

```bash
# .env file (or set in PowerShell)
DOCUMENTINTELLIGENCE_ENDPOINT=https://<your-instance>.cognitiveservices.azure.com/
DOCUMENTINTELLIGENCE_API_KEY=<your-api-key>
```

**PowerShell (Development)**:
```powershell
$env:DOCUMENTINTELLIGENCE_ENDPOINT = "https://kraftd-doc-intelligence.cognitiveservices.azure.com/"
$env:DOCUMENTINTELLIGENCE_API_KEY = "your-api-key-here"
```

### 3. Verify Configuration

```python
# In Python, check if Azure is configured:
from document_processing import is_azure_configured, get_azure_service

if is_azure_configured():
    service = get_azure_service()
    print("Azure Document Intelligence is configured and ready!")
else:
    print("Azure not configured, using local extraction.")
```

## How It Works

### Extraction Flow

```
Document Upload
    ↓
/extract endpoint
    ↓
Check Azure credentials?
    ├─ YES → Try Azure Document Intelligence
    │   ├─ Success → Use Azure results (High Accuracy ~95%+)
    │   └─ Failure → Fall back to local extraction
    │
    └─ NO → Use local pattern-based extraction (Good Accuracy ~80%)
    ↓
Map results to KraftdDocument schema
    ↓
Calculate data quality & completeness scores
    ↓
Return structured document data
```

### Azure Document Intelligence Models

The system uses **"prebuilt-layout"** model which:
- Extracts text, tables, paragraphs, and structure
- Detects language, handwriting, and styles
- Returns high-confidence extraction results
- Handles complex layouts (scanned, poor quality, multi-column, etc.)

**Optional: Use Specialized Models**

For even better results on specific document types, you can modify the model selection:

```python
# In main.py extract endpoint, change:
model_type = "prebuilt-layout"  # Current

# To one of these for better accuracy:
model_type = "prebuilt-invoice"  # For invoices
model_type = "prebuilt-receipt"  # For receipts
model_type = "prebuilt-document"  # For general documents
```

## Code Integration

### In `document_processing/azure_service.py`

```python
from document_processing import is_azure_configured, get_azure_service

# Check if configured
if is_azure_configured():
    service = get_azure_service()
    
    # Analyze document
    result = service.analyze_document("/path/to/document.pdf")
    
    # Extract different components
    text = service.get_document_text(result)
    tables = service.extract_tables(result)
    lines = service.extract_text_by_lines(result)
    fields = service.extract_form_fields(result)
```

### In `main.py` extract endpoint

The endpoint automatically:
1. Tries Azure if configured
2. Falls back to local if Azure fails or isn't configured
3. Reports which method was used in `extraction_method` field

## Pricing

Azure Document Intelligence pricing:
- **First 100 pages/month**: Free
- **Pages 101-500,000**: $0.50 per page
- **Pages 500,001+**: $0.25 per page

For procurement documents with tables and complex layouts, expect:
- RFQ: 1-3 pages
- Quotation: 2-4 pages
- PO: 1-2 pages
- Contract: 5-20+ pages

**Cost Example**: 1000 RFQs = 2000 pages = **$1000/month** at typical rates

## Troubleshooting

### Error: "Azure Document Intelligence credentials not configured"

**Solution**: Set environment variables and restart the server.

```powershell
# Test in PowerShell:
$env:DOCUMENTINTELLIGENCE_ENDPOINT
$env:DOCUMENTINTELLIGENCE_API_KEY
```

### Error: "Azure extraction failed: 403 Unauthorized"

**Solution**: Check your API key and endpoint are correct.

```powershell
# Verify in Azure Portal > Document Intelligence resource > Keys and Endpoint
```

### Azure extraction is slow (30+ seconds)

**Solution**: This is normal for first request as the service initializes. Subsequent requests are faster.

## Monitoring

Check extraction method in responses:

```python
# Response includes:
{
    "extraction_method": "direct_parse",  # Local pattern-based
    # OR
    "extraction_method": "ai_extraction",  # Azure Document Intelligence
    
    "processing_metadata": {
        "processing_duration_ms": 450,  # Time taken
        "source_file_size_bytes": 125000
    }
}
```

## Future Improvements

- **Custom Models**: Train custom Document Intelligence models for specific RFQ formats
- **Document Classification**: Auto-detect document type before choosing model
- **Batch Processing**: Submit multiple documents for parallel extraction
- **Cost Optimization**: Implement hybrid approach (Azure for complex docs, local for simple)

## Reference

- [Azure Document Intelligence Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Python SDK Reference](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-documentintelligence-readme)
- [Pricing Calculator](https://azure.microsoft.com/en-us/pricing/details/ai-document-intelligence/)
