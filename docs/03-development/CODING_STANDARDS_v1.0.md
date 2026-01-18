# Coding Standards Document

**Version:** 1.0  
**Status:** APPROVED  
**Enforcement:** Automated + Code Review  
**Last Updated:** 2026-01-17

---

## Python Backend Standards

### Code Style (PEP 8)

**Formatting:**
```python
# Good: Clear and following conventions
async def process_document(
    document_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> DocumentResponse:
    """Process uploaded document through extraction pipeline."""
    pass

# Bad: Too long, unclear naming
async def p_d(did,uid,cu=Depends(get_current_user)):
    pass
```

**Line Length:**
- Maximum: 100 characters
- Exception: URLs and imports can exceed

**Imports:**
```python
# Order: Standard library → Third-party → Local
import asyncio
import os
from datetime import datetime

import fastapi
from pydantic import BaseModel

from .services import document_service
from .repositories import DocumentRepository
```

**Naming Conventions:**

| Type | Convention | Example |
|------|-----------|---------|
| Variables | snake_case | `document_id`, `user_email` |
| Functions | snake_case | `process_document()` |
| Classes | PascalCase | `DocumentService`, `UserRepository` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE = 5_000_000` |
| Private | _leading_underscore | `_internal_helper()` |

### Type Hints (Required)

```python
# Good: All types annotated
async def upload_document(
    file: UploadFile,
    user_id: str,
    document_type: Optional[str] = None
) -> DocumentResponse:
    """Upload and process document."""
    return response

# Bad: Missing type hints
async def upload_document(file, user_id, document_type=None):
    return response
```

### Documentation

```python
def extract_line_items(document_id: str) -> List[LineItem]:
    """
    Extract line items from procurement document.
    
    Args:
        document_id: Unique identifier for the document
        
    Returns:
        List of extracted line items with confidence scores
        
    Raises:
        DocumentNotFoundError: If document not found
        ExtractionFailedError: If extraction service fails
        
    Example:
        >>> items = await extract_line_items("doc_123")
        >>> print(items[0].description)
        "Frontend Development"
    """
    pass
```

### Error Handling

```python
# Good: Specific exception handling
try:
    result = await document_intelligence_client.extract(file)
except DocumentIntelligenceException as e:
    logger.error(f"Extraction failed: {e}")
    raise ExtractionFailedError(f"Failed to extract: {str(e)}") from e

# Bad: Generic exception handling
try:
    result = await document_intelligence_client.extract(file)
except:
    pass  # Silently ignore errors
```

### Testing

```python
# backend/tests/test_auth_service.py
import pytest
from services.auth_service import AuthService

class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        return AuthService()
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, auth_service):
        # Arrange
        email = "user@example.com"
        password = "ValidPass123!"
        
        # Act
        result = await auth_service.login(email, password)
        
        # Assert
        assert result.access_token is not None
        assert result.token_type == "bearer"
```

### Async/Await

```python
# Good: All I/O operations async
async def get_documents(user_id: str) -> List[Document]:
    return await document_repository.find_by_user(user_id)

# Bad: Blocking I/O in async function
async def get_documents(user_id: str) -> List[Document]:
    return document_repository.find_by_user(user_id)  # Blocking!
```

---

## TypeScript/React Frontend Standards

### Code Style (ESLint + Prettier)

**Formatting:**
```typescript
// Good: Consistent, readable
interface DocumentCardProps {
  document: Document;
  onSelect: (id: string) => void;
  isSelected: boolean;
}

const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onSelect,
  isSelected
}) => {
  return (
    <div className="card">
      <h3>{document.filename}</h3>
      <p>{document.status}</p>
    </div>
  );
};

// Bad: Inconsistent formatting
const DocumentCard=(doc,onSelect,isSelected)=><div><h3>{doc.filename}</h3></div>;
```

**Naming Conventions:**

| Type | Convention | Example |
|------|-----------|---------|
| Variables | camelCase | `documentId`, `userEmail` |
| Functions | camelCase | `handleDocumentSelect()` |
| Components | PascalCase | `DocumentCard`, `Dashboard` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE = 5_000_000` |
| Private | _leading_underscore | `_internalHelper()` |
| Interfaces | PascalCase | `DocumentProps`, `APIResponse` |

### Type Safety

```typescript
// Good: Strict typing, no any
interface Document {
  document_id: string;
  filename: string;
  status: 'uploading' | 'extracting' | 'extracted';
  uploaded_at: Date;
}

const handleDocumentSelect = (doc: Document): void => {
  console.log(doc.filename);
};

// Bad: Using any
const handleDocumentSelect = (doc: any): void => {
  console.log(doc.filename);
};
```

### React Patterns

```typescript
// Good: Functional component with hooks
const DocumentList: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    fetchDocuments();
  }, []);
  
  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await api.getDocuments();
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to fetch documents', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  if (isLoading) return <LoadingSpinner />;
  return (
    <div>
      {documents.map(doc => (
        <DocumentCard key={doc.document_id} document={doc} />
      ))}
    </div>
  );
};

// Bad: Class component, complex lifecycle
class DocumentList extends React.Component {
  componentDidMount() { }
  componentWillUnmount() { }
}
```

### Component Organization

```typescript
// Good structure: functional > hooks > JSX
export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onSelect
}) => {
  // 1. State
  const [isHovered, setIsHovered] = useState(false);
  
  // 2. Effects
  useEffect(() => {
    // initialization
  }, []);
  
  // 3. Handlers
  const handleClick = () => {
    onSelect(document.document_id);
  };
  
  // 4. Render
  return (
    <div onMouseEnter={() => setIsHovered(true)}>
      {/* JSX */}
    </div>
  );
};
```

### Error Handling

```typescript
// Good: Proper error handling
async function uploadDocument(file: File): Promise<void> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload', formData);
    setDocument(response.data);
  } catch (error) {
    if (error instanceof ValidationError) {
      showError('Invalid file type');
    } else if (error instanceof APIError) {
      showError('Upload failed, please try again');
    } else {
      showError('An unexpected error occurred');
    }
  }
}

// Bad: No error handling
async function uploadDocument(file: File) {
  const response = await api.post('/documents/upload', file);
  setDocument(response.data);
}
```

### CSS/Styling

```typescript
// Good: Component-scoped styles
import styles from './DocumentCard.module.css';

const DocumentCard = () => (
  <div className={styles.card}>
    <h3 className={styles.title}>Document</h3>
  </div>
);

/* DocumentCard.module.css */
.card {
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

// Bad: Global styles, hard to maintain
const DocumentCard = () => (
  <div style={{ padding: '1rem', border: '1px solid #e0e0e0' }}>
    <h3>Document</h3>
  </div>
);
```

---

## API Design Standards

### Endpoint Naming

```
# Good: RESTful, resource-based
POST   /api/v1/documents              # Create
GET    /api/v1/documents              # List
GET    /api/v1/documents/{id}         # Get
PATCH  /api/v1/documents/{id}         # Update
DELETE /api/v1/documents/{id}         # Delete

# Bad: Action-based, non-RESTful
GET  /api/documents/create
GET  /api/documents/list
POST /api/documents/delete
```

### Request/Response Format

```json
// Good: Consistent, documented
{
  "document_id": "doc_abc123",
  "filename": "RFQ_2026.pdf",
  "status": "extracted",
  "extracted_confidence": 0.96,
  "line_items": [
    {
      "description": "Frontend",
      "hours": 100,
      "rate": 150
    }
  ]
}

// Bad: Inconsistent, missing fields
{
  "id": "abc123",
  "name": "RFQ_2026.pdf",
  "st": "extracted",
  "conf": 96
}
```

### Error Responses

```json
// Good: Consistent error format
{
  "error": "validation_error",
  "message": "Invalid email format",
  "details": {
    "email": "must be valid email address"
  },
  "timestamp": "2026-01-17T10:30:00Z"
}

// Bad: Inconsistent
{
  "status": "error",
  "msg": "Email is bad"
}
```

---

## Commit & PR Standards

### Git Commits

```bash
# Good: Clear, imperative mood
git commit -m "Add document extraction API endpoint"
git commit -m "Fix JWT token expiration validation"
git commit -m "Refactor document service for clarity"

# Bad: Unclear, passive voice
git commit -m "Fixed stuff"
git commit -m "Updated components"
git commit -m "WIP: does something"
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>

# Example:
feat(documents): add bulk upload capability

Allow users to upload multiple documents in a single request.
Implement progress tracking for batch uploads.

Closes #123
```

**Types:** feat, fix, docs, style, refactor, test, chore

### Pull Request Standards

```markdown
## Description
Clear description of what this PR does

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Manual testing completed
- [ ] No regressions detected

## Screenshots
(If applicable)

## Related Issues
Closes #123
```

---

## Linting & Formatting

### Backend

```bash
# Format code with Black
black .

# Check with Flake8
flake8 .

# Type check with MyPy
mypy .

# Run tests
pytest --cov=.
```

### Frontend

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Type check
npm run type-check

# Run tests
npm run test
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

---

## Code Review Checklist

- [ ] Code follows style guide
- [ ] No unused imports or variables
- [ ] Types properly annotated
- [ ] Error handling present
- [ ] Tests included
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Performance acceptable
- [ ] Security considerations addressed
- [ ] Commit messages clear

---

## Tool Configuration

### .editorconfig
```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4
```

### VS Code Settings
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode"
}
```

---

## Performance Standards

**Code Quality:**
- Cyclomatic complexity < 10
- Function length < 50 lines
- Class length < 200 lines

**Performance:**
- API response time < 500ms (p95)
- Page load time < 2s
- Bundle size < 500KB (gzipped)
- Database query < 100ms

---

**Reference:** `/docs/03-development/CODING_STANDARDS_v1.0.md`
