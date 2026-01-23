# KraftdIntel AI Coding Guidelines

## Architecture Overview
KraftdIntel is a supply chain intelligence platform with:
- **Backend**: FastAPI (Python) with document processing, AI agent orchestration, and Cosmos DB persistence
- **Frontend**: React 18 + TypeScript + Vite, deployed to Azure Static Web Apps
- **Infrastructure**: Azure Container Apps, Cosmos DB, Document Intelligence, OpenAI
- **Data Flow**: Documents → Azure DI extraction → AI agent processing → Cosmos DB storage → React dashboard

## Critical Developer Workflows

### Local Development
- Backend: `cd backend && uvicorn main:app --reload` (port 8000)
- Frontend: `cd frontend && npm run dev` (port 3000)
- Tests: `cd backend && python -m pytest` (uses pytest.ini config)
- Docker: `cd backend && docker build -t kraftd-backend .` then `docker run -p 8000:8000 kraftd-backend`

### Deployment
- Use `deploy-azure.bat` or `deploy-azure.sh` for full Azure deployment
- Backend deploys to Azure Container Apps with Docker
- Frontend uses Azure Static Web Apps with GitHub Actions
- Environment variables in `.env` (copy from `.env.example`)

### Debugging
- Check logs: `docker logs <container>` or Azure portal
- Test endpoints: Use `test_cosmos_connection.py` for DB, `unit_tests.py` for API
- Agent issues: Verify Azure OpenAI credentials in `.env`

## Project-Specific Conventions

### Backend Patterns
- **Async everywhere**: All service methods use `async/await` (e.g., `await self.cosmos.create_item()`)
- **Error handling**: Raise `HTTPException(status_code=404, detail="Not found")` with appropriate status codes
- **Logging**: Use `logger.info()`, `logger.error()`, `logger.warning()` from Python logging module
- **Services**: Business logic in `backend/services/` classes (e.g., `ConversionsService`, `SchemaService`)
- **Models**: Pydantic models for request/response validation
- **Cosmos DB**: Partition key is `user_email` for multi-tenancy; use async CRUD methods

### Frontend Patterns
- **Auth context**: Use `useAuth()` hook for authentication state
- **API calls**: Use `apiClient` from `services/api.ts` with automatic token refresh
- **Components**: Functional components with TypeScript interfaces
- **Routing**: React Router with protected routes using `ProtectedRoute` wrapper
- **State**: Context providers for global state (auth, etc.)

### Code Examples
```python
# Backend service method
async def create_conversion(self, user_email: str, data: dict) -> dict:
    try:
        result = await self.cosmos.create_item('conversions', {
            'id': str(uuid.uuid4()),
            'user_email': user_email,
            'data': data,
            'created_at': datetime.utcnow().isoformat()
        })
        logger.info(f"Created conversion for {user_email}")
        return result
    except CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail="Conversion already exists")
```

```tsx
// Frontend component
const Dashboard = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const docs = await apiClient.getDocuments();
        setDocuments(docs);
      } catch (error) {
        console.error('Failed to load documents:', error);
      }
    };
    loadDocuments();
  }, []);

  return (
    <Layout>
      <h1>Welcome {user?.email}</h1>
      {documents.map(doc => <DocumentCard key={doc.id} document={doc} />)}
    </Layout>
  );
};
```

## Integration Points
- **Azure Document Intelligence**: Handles PDF/Word/Excel extraction (95%+ accuracy)
- **Azure OpenAI**: Powers AI agent reasoning via Microsoft Agent Framework
- **Cosmos DB**: NoSQL storage with multi-tenant partitioning by `user_email`
- **Azure Static Web Apps**: Frontend hosting with CI/CD
- **Azure Container Apps**: Backend containerized deployment

## Key Files to Reference
- `backend/main.py`: FastAPI app entry point and routes
- `backend/services/conversions_service.py`: Example service with Cosmos integration
- `frontend/src/context/AuthContext.tsx`: Authentication state management
- `frontend/src/services/api.ts`: Backend API client
- `infrastructure/main.bicep`: Azure infrastructure as code
- `DEPLOYMENT_GUIDE.md`: Complete deployment instructions
- `PROJECT_STRUCTURE.md`: Detailed folder organization</content>
<parameter name="filePath">c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\.github\copilot-instructions.md