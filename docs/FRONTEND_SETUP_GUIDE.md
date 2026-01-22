# Frontend Deployment Guide - KraftdIntel

**Date:** January 15, 2026  
**Status:** Ready for deployment  
**Hosting:** Azure Static Web App  

---

## Quick Start (5 minutes)

### 1. Prerequisites
```bash
✅ Node.js 18+ installed
✅ GitHub account with repo push access
✅ Azure subscription
```

### 2. Local Setup
```bash
cd frontend
npm install
npm run dev
```

**App available at:** http://localhost:3000

### 3. Deploy to Azure Static Web App

#### Option A: Using Azure Portal (Recommended for first time)
```
1. Go to Azure Portal
2. Search "Static Web Apps"
3. Click "Create"
4. Connect to GitHub
5. Select this repository
6. Build preset: React
7. App location: frontend
8. Build output location: dist
9. Click "Create"
```

#### Option B: Using Azure CLI
```powershell
az staticwebapp create `
  --name kraftdintel-web `
  --resource-group kraftdintel-rg `
  --source https://github.com/YOUR_USERNAME/KraftdIntel `
  --location uaenorth `
  --branch main `
  --app-location frontend `
  --output-location dist
```

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   └── Layout.css
│   ├── context/
│   │   └── AuthContext.tsx          (State management)
│   ├── pages/
│   │   ├── Login.tsx                (Authentication page)
│   │   ├── Login.css
│   │   ├── Dashboard.tsx            (Main app)
│   │   └── Dashboard.css
│   ├── services/
│   │   └── api.ts                   (Backend integration)
│   ├── types/
│   │   └── index.ts                 (Type definitions)
│   ├── styles/
│   │   └── index.css                (Global styles)
│   ├── App.tsx                      (Main component)
│   └── main.tsx                     (Entry point)
├── public/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── staticwebapp.config.json         (Static Web App config)
└── .env.example
```

---

## Development

### Available Scripts

```bash
# Start dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run lint
```

### Environment Variables

Create `.env.local`:
```
VITE_API_URL=https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

**For Static Web App deployment**, env vars are auto-configured via GitHub Actions.

---

## Features Implemented

### ✅ Authentication
- Login with email/password
- Registration/signup
- JWT token management
- Auto-token refresh
- Persistent sessions

### ✅ Document Management
- Upload documents
- List documents
- View document status
- Delete documents
- Update document metadata

### ✅ Workflow Management
- Start procurement workflow
- Track workflow status
- View workflow steps
- Update workflow status

### ✅ API Integration
- Axios client with interceptors
- Automatic token injection
- Error handling & retry logic
- Request/response transformation

### ✅ UI/UX
- Modern gradient design
- Responsive layout (mobile-friendly)
- Form validation
- Loading states
- Error messages
- Success feedback

---

## API Integration Details

### Backend URL (Production)
```
https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

### Configured Endpoints
```
Authentication:
  POST   /auth/register         (Create account)
  POST   /auth/login            (Sign in)
  POST   /auth/refresh-token    (Refresh JWT)

Documents:
  POST   /documents/upload      (Upload file)
  GET    /documents             (List all)
  GET    /documents/{id}        (Get one)
  PUT    /documents/{id}        (Update)
  DELETE /documents/{id}        (Delete)

Workflows:
  POST   /workflows/start       (Initiate)
  GET    /workflows/{id}        (Get status)
  PUT    /workflows/{id}/status (Update)
```

All requests include JWT Bearer token automatically.

---

## Deployment Pipeline

### GitHub Actions Workflow
```
Trigger: Push to main branch in /frontend directory

Steps:
  1. Checkout code
  2. Setup Node.js 18
  3. Install dependencies
  4. Build (Vite)
  5. Deploy to Static Web App (auto)
```

### Deployment Flow
```
Code Push → GitHub Actions → Build → Deploy to Azure → Live
```

**Deployment time:** 2-5 minutes

---

## Configuration

### Static Web App Config (`staticwebapp.config.json`)
```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/api/*", "/*.{json,jpg,...}"]
  }
}
```

This ensures:
- ✅ React Router SPA works (client-side routing)
- ✅ API requests pass through to backend
- ✅ Static assets served correctly

---

## Testing Locally

### 1. Start Backend
```powershell
# In backend folder
python -m uvicorn main:app --reload
```
Backend: http://localhost:8000

### 2. Start Frontend
```powershell
# In frontend folder
npm run dev
```
Frontend: http://localhost:3000

### 3. Test Authentication
```
Email: test@example.com
Password: test123
```

**Create test account:** First time? Use "Register" button

### 4. Test Features
- Upload a PDF or image
- Start workflow
- Check dashboard updates

---

## Production Checklist

Before going live:

- [ ] Environment variables configured in Static Web App
- [ ] API endpoint URL set correctly
- [ ] CORS enabled on backend (already done)
- [ ] SSL/TLS working (auto with Azure)
- [ ] DNS/custom domain configured (optional)
- [ ] Error tracking enabled (optional)

---

## Performance Optimizations

### Built-in
```
✅ Code splitting (Vite)
✅ Tree shaking
✅ CSS minification
✅ JS minification
✅ Gzip compression
✅ CDN caching (Static Web App)
```

### Recommended
```
⚠️  Add image optimization (lazy loading)
⚠️  Implement error boundary component
⚠️  Add loading spinners for better UX
```

---

## Troubleshooting

### "API requests failing"
```
✓ Check backend is running
✓ Verify API_URL in .env
✓ Check CORS on backend (already configured)
✓ Clear browser cache (Ctrl+Shift+Delete)
```

### "Blank page after login"
```
✓ Check browser console for errors (F12)
✓ Verify token in localStorage (DevTools > Application)
✓ Try clearing localStorage and re-login
```

### "Build failed in GitHub Actions"
```
✓ Check Node version (should be 18+)
✓ Check dependencies in package.json
✓ Run 'npm ci' locally to verify lock file
✓ Check for TypeScript errors: npm run lint
```

---

## Monitoring & Logs

### Static Web App Dashboard
```
Azure Portal → Static Web Apps → kraftdintel-web → Activity log
```

### Error Tracking
```
Real-time logs available in Azure Portal
Auto-configured with deployment
```

---

## Next Steps

1. ✅ Deploy to Static Web App (this guide)
2. ✅ Test all features in production
3. ✅ Monitor error logs for 1 week
4. ✅ Collect user feedback
5. ✅ Optimize based on performance data

---

## Support

**Backend API Documentation:** See `API_DOCUMENTATION.md`  
**Infrastructure Setup:** See `INFRASTRUCTURE_AUDIT.md`  
**Deployment Guide (Backend):** See `PRIORITY_4_DEPLOYMENT_GUIDE.md`  

---

**Frontend: Ready to Deploy** ✅

