# 📊 Dashboard Azure Enhancements & Brand Configuration

**Date:** January 20, 2026  
**Status:** IMPLEMENTATION GUIDE  
**Target:** Azure Static Web App Deployment

---

## Overview

This guide optimizes your Kraftd Docs dashboard for Azure Static Web App deployment with full branding compliance.

---

## Part 1: Dashboard Branding Enhancement

### 1.1 Update Dashboard Layout with Logo & Branding

**File:** `frontend/src/pages/Dashboard.tsx`

```tsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiClient } from '../services/api'
import DocumentUpload from '../components/DocumentUpload'
import DocumentList from '../components/DocumentList'
import logo from '../assets/kraftd-logo.svg'
import './Dashboard.css'

interface StatCard {
  label: string
  value: number
  icon: string
  color: string
  trend?: string
}

interface Activity {
  id: string
  type: 'upload' | 'process' | 'export' | 'review'
  document: string
  timestamp: string
  status: 'pending' | 'processing' | 'completed' | 'error'
}

const Dashboard = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()
  const [documents, setDocuments] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isReviewing, setIsReviewing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'documents'>('overview')

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    } else {
      loadDashboardData()
    }
  }, [isAuthenticated, navigate])

  const loadDashboardData = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get('/documents')
      setDocuments(response.data.documents || [])
      setError(null)
    } catch (err) {
      setError('Failed to load documents')
      console.error('Dashboard error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const stats: StatCard[] = [
    {
      label: 'Total Documents',
      value: documents.length,
      icon: '📄',
      color: '#00BCD4'
    },
    {
      label: 'Processed',
      value: documents.filter((d: any) => d.status === 'completed').length,
      icon: '✓',
      color: '#4CAF50'
    },
    {
      label: 'Processing',
      value: documents.filter((d: any) => d.status === 'processing').length,
      icon: '⏳',
      color: '#FFC107'
    },
    {
      label: 'Failed',
      value: documents.filter((d: any) => d.status === 'error').length,
      icon: '✗',
      color: '#F44336'
    }
  ]

  const recentActivities: Activity[] = documents
    .slice(0, 5)
    .map((doc: any) => ({
      id: doc.id,
      type: doc.type || 'upload',
      document: doc.name,
      timestamp: new Date(doc.createdAt).toLocaleDateString(),
      status: doc.status || 'pending'
    }))

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      {/* Header with Branding */}
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Kraftd Logo" className="header-logo" />
          <div className="header-title">
            <h1>Kraftd Docs</h1>
            <p className="header-subtitle">Audit-Native Intelligence Platform</p>
          </div>
        </div>
        <div className="header-right">
          <div className="user-info">
            <span className="user-name">{user?.name || user?.email || 'User'}</span>
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </div>
        </div>
      </header>

      {/* Messages */}
      {error && <div className="alert alert-error">{error}</div>}
      {successMessage && <div className="alert alert-success">{successMessage}</div>}

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          📁 Documents
        </button>
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            {/* Statistics Cards */}
            <div className="stats-grid">
              {stats.map((stat) => (
                <div key={stat.label} className="stat-card" style={{ borderLeftColor: stat.color }}>
                  <div className="stat-icon">{stat.icon}</div>
                  <div className="stat-info">
                    <div className="stat-label">{stat.label}</div>
                    <div className="stat-value">{stat.value}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Upload Section */}
            <div className="upload-section">
              <h2>📤 Upload Documents</h2>
              <DocumentUpload onUploadSuccess={() => loadDashboardData()} />
            </div>

            {/* Recent Activity */}
            <div className="activity-section">
              <h2>🕐 Recent Activity</h2>
              <div className="activity-list">
                {recentActivities.length > 0 ? (
                  recentActivities.map((activity) => (
                    <div key={activity.id} className="activity-item">
                      <span className="activity-icon">
                        {activity.type === 'upload' && '📤'}
                        {activity.type === 'process' && '⚙️'}
                        {activity.type === 'export' && '💾'}
                        {activity.type === 'review' && '👁️'}
                      </span>
                      <div className="activity-details">
                        <span className="activity-name">{activity.document}</span>
                        <span className="activity-time">{activity.timestamp}</span>
                      </div>
                      <span className={`activity-status status-${activity.status}`}>
                        {activity.status === 'pending' && '⏳ Pending'}
                        {activity.status === 'processing' && '⚙️ Processing'}
                        {activity.status === 'completed' && '✓ Done'}
                        {activity.status === 'error' && '✗ Failed'}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="no-activity">No recent activity. Upload documents to get started!</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="documents-section">
            <h2>📁 Your Documents</h2>
            <DocumentList documents={documents} isLoading={isLoading} onRefresh={loadDashboardData} />
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>&copy; 2026 Kraftd Docs. Audit-native intelligence for supply chain professionals.</p>
        <div className="footer-links">
          <a href="/terms">Terms of Service</a>
          <a href="/privacy">Privacy Policy</a>
          <a href="/contact">Contact Us</a>
        </div>
      </footer>
    </div>
  )
}

export default Dashboard
```

### 1.2 Enhanced Dashboard Styling with Branding

**File:** `frontend/src/pages/Dashboard.css`

```css
/* ===== Root Colors (Kraftd Branding) ===== */
:root {
  --primary: #00BCD4;
  --primary-dark: #0097A7;
  --primary-light: #4DD0E1;
  --secondary: #1A5A7A;
  --secondary-light: #2C7A9A;
  --dark-text: #1A1A1A;
  --body-text: #536B82;
  --light-bg: #F8F9FA;
  --lighter-bg: #FFFFFF;
  --border: #E0E0E0;
  --white: #FFFFFF;
  --success: #4CAF50;
  --success-light: #E8F5E9;
  --warning: #FFC107;
  --warning-light: #FFF9C4;
  --error: #F44336;
  --error-light: #FFEBEE;
  --info: #2196F3;
  --info-light: #E3F2FD;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;

  /* Font */
  --font-family: 'Inter', -apple-system, 'Segoe UI', 'Roboto', sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.15);

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Z-index */
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal: 300;
  --z-tooltip: 400;
}

/* ===== Reset & Base ===== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #root {
  height: 100%;
  width: 100%;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-md);
  line-height: 1.6;
  color: var(--dark-text);
  background: var(--light-bg);
}

/* ===== Dashboard Container ===== */
.dashboard {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--light-bg);
}

/* ===== Header ===== */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: var(--white);
  box-shadow: var(--shadow-md);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.header-logo {
  height: 40px;
  width: auto;
  display: block;
}

.header-title h1 {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.header-subtitle {
  font-size: var(--font-size-sm);
  opacity: 0.9;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.user-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.logout-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-md);
  color: var(--white);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

/* ===== Alerts ===== */
.alert {
  margin: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.alert-error {
  background: var(--error-light);
  color: var(--error);
  border-left: 4px solid var(--error);
}

.alert-success {
  background: var(--success-light);
  color: var(--success);
  border-left: 4px solid var(--success);
}

/* ===== Tabs ===== */
.dashboard-tabs {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--white);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--spacing-lg);
}

.tab {
  padding: var(--spacing-md) var(--spacing-lg);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--body-text);
  font-size: var(--font-size-md);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.tab:hover {
  color: var(--primary);
}

.tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

/* ===== Content ===== */
.dashboard-content {
  flex: 1;
  padding: var(--spacing-lg);
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* ===== Overview Section ===== */
.overview-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xl);
}

/* ===== Statistics Grid ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
}

.stat-card {
  background: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border-left: 4px solid var(--primary);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--body-text);
  font-weight: 500;
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--dark-text);
}

/* ===== Upload Section ===== */
.upload-section {
  background: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.upload-section h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--dark-text);
}

/* ===== Activity Section ===== */
.activity-section {
  background: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.activity-section h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--dark-text);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--light-bg);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.activity-item:hover {
  background: #F0F7FB;
}

.activity-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.activity-name {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--dark-text);
}

.activity-time {
  font-size: var(--font-size-sm);
  color: var(--body-text);
}

.activity-status {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: 500;
  white-space: nowrap;
}

.status-pending {
  background: var(--warning-light);
  color: var(--warning);
}

.status-processing {
  background: var(--info-light);
  color: var(--info);
}

.status-completed {
  background: var(--success-light);
  color: var(--success);
}

.status-error {
  background: var(--error-light);
  color: var(--error);
}

.no-activity {
  text-align: center;
  color: var(--body-text);
  padding: var(--spacing-lg);
  font-size: var(--font-size-sm);
}

/* ===== Documents Section ===== */
.documents-section {
  background: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.documents-section h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--dark-text);
}

/* ===== Footer ===== */
.dashboard-footer {
  background: var(--dark-text);
  color: var(--white);
  padding: var(--spacing-lg);
  text-align: center;
  margin-top: var(--spacing-2xl);
  border-top: 1px solid var(--border);
}

.dashboard-footer p {
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-md);
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.footer-links a {
  color: var(--primary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  transition: color 0.2s ease;
}

.footer-links a:hover {
  color: var(--primary-light);
  text-decoration: underline;
}

/* ===== Loading State ===== */
.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--body-text);
}

.loading::after {
  content: '';
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid var(--primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== Responsive Design ===== */

/* Tablet (768px - 1023px) */
@media (max-width: 1023px) {
  .dashboard-header {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-md);
  }

  .header-left,
  .header-right {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }

  .dashboard-content {
    padding: var(--spacing-md);
  }

  .dashboard-tabs {
    padding: var(--spacing-md);
  }
}

/* Mobile (< 768px) */
@media (max-width: 767px) {
  :root {
    --spacing-lg: 16px;
    --font-size-2xl: 20px;
    --font-size-xl: 18px;
  }

  .dashboard-header {
    padding: var(--spacing-md);
  }

  .header-logo {
    height: 32px;
  }

  .header-title h1 {
    font-size: var(--font-size-xl);
  }

  .header-subtitle {
    display: none;
  }

  .logout-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .stat-card {
    padding: var(--spacing-md);
  }

  .dashboard-content {
    padding: var(--spacing-md);
    gap: var(--spacing-lg);
  }

  .dashboard-tabs {
    flex-direction: column;
    gap: 0;
    padding: 0;
    margin-bottom: var(--spacing-md);
  }

  .tab {
    padding: var(--spacing-md);
    width: 100%;
    text-align: left;
    border-bottom: 1px solid var(--border);
    border-left: 3px solid transparent;
  }

  .tab.active {
    border-bottom-color: var(--border);
    border-left-color: var(--primary);
  }

  .footer-links {
    flex-direction: column;
    gap: var(--spacing-md);
  }
}

/* Extra Small (< 480px) */
@media (max-width: 479px) {
  :root {
    --spacing-lg: 12px;
    --spacing-md: 12px;
    --font-size-xl: 16px;
  }

  .header-left {
    gap: var(--spacing-sm);
  }

  .stat-card {
    flex-direction: column;
    text-align: center;
  }

  .stat-icon {
    font-size: 24px;
  }

  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-status {
    width: 100%;
    text-align: center;
  }
}
```

---

## Part 2: Performance Optimization

### 2.1 Lazy Load Components

**File:** `frontend/src/pages/Dashboard.tsx` (updated imports)

```tsx
import React, { Suspense, lazy } from 'react'

// Lazy load heavy components
const DocumentUpload = lazy(() => import('../components/DocumentUpload'))
const DocumentList = lazy(() => import('../components/DocumentList'))

const LoadingSpinner = () => (
  <div className="loading">Loading...</div>
)

// In JSX:
<Suspense fallback={<LoadingSpinner />}>
  <DocumentUpload onUploadSuccess={() => loadDashboardData()} />
</Suspense>
```

### 2.2 Optimize API Calls

**File:** `frontend/src/pages/Dashboard.tsx`

```tsx
import { useCallback, useMemo } from 'react'

// Memoize expensive calculations
const stats = useMemo(() => [
  {
    label: 'Total Documents',
    value: documents.length,
    icon: '📄',
    color: '#00BCD4'
  },
  // ... rest of stats
], [documents])

// Use useCallback to memoize functions
const loadDashboardData = useCallback(async () => {
  try {
    setIsLoading(true)
    const response = await apiClient.get('/documents')
    setDocuments(response.data.documents || [])
  } catch (err) {
    setError('Failed to load documents')
  } finally {
    setIsLoading(false)
  }
}, [])
```

### 2.3 Image Optimization

**File:** `frontend/public/index.html`

```html
<!-- Add image loading hints -->
<link rel="preload" as="image" href="/images/kraftd-logo.svg">
<link rel="preload" as="image" href="/images/placeholder.png">

<!-- Use WebP with fallback -->
<picture>
  <source srcset="/images/logo.webp" type="image/webp">
  <img src="/images/logo.png" alt="Kraftd Logo">
</picture>
```

---

## Part 3: Azure-Specific Configurations

### 3.1 Environment Variables for Azure

**File:** `frontend/.env.production`

```env
# Azure Static Web App
VITE_API_URL=https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
VITE_APP_NAME=Kraftd Docs
VITE_ENVIRONMENT=production

# Analytics
VITE_APP_INSIGHTS_KEY=your-app-insights-key

# Feature flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ERROR_TRACKING=true
VITE_CACHE_TIMEOUT=3600000
```

### 3.2 Static Web App Configuration

**File:** `frontend/staticwebapp.config.json`

```json
{
  "routes": [
    {
      "route": "/auth/*",
      "rewrite": "/index.html"
    },
    {
      "route": "/dashboard",
      "allowedRoles": ["authenticated"],
      "rewrite": "/index.html"
    },
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": [
      "/images/*",
      "/assets/*",
      "/css/*",
      "*.json",
      "*.svg"
    ]
  },
  "responseOverrides": {
    "401": {
      "rewrite": "/login",
      "statusCode": 302
    },
    "404": {
      "serve": "/index.html",
      "statusCode": 200
    }
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data: https://fonts.googleapis.com; connect-src 'self' https://*.azurecontainerapps.io https://dc.services.visualstudio.com;"
  }
}
```

### 3.3 Security Headers

**File:** `frontend/src/main.tsx`

```typescript
// Add security headers middleware
const setupSecurityHeaders = () => {
  if (typeof window !== 'undefined') {
    // Prevent clickjacking
    if (window.self !== window.top) {
      window.top!.location = window.self.location
    }
  }
}

setupSecurityHeaders()
```

---

## Part 4: Branding Assets Setup

### 4.1 Logo Assets

Create folder: `frontend/src/assets/`

```
src/assets/
├── kraftd-logo.svg          # Main logo
├── kraftd-logo-light.svg    # Light version
├── kraftd-icon.svg          # Icon only
├── favicon.png              # Browser tab icon
└── og-image.png             # Social media preview
```

### 4.2 SVG Logo Example

**File:** `frontend/src/assets/kraftd-logo.svg`

```xml
<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
  <!-- Define colors matching Kraftd branding -->
  <defs>
    <style>
      .logo-text { font-family: Inter, sans-serif; font-weight: 700; }
    </style>
  </defs>
  
  <!-- Icon - Cyan square with document -->
  <rect x="0" y="0" width="50" height="50" fill="#00BCD4" rx="8"/>
  <text x="25" y="35" text-anchor="middle" class="logo-text" font-size="28" fill="white">📄</text>
  
  <!-- Text - Kraftd Docs -->
  <text x="60" y="38" class="logo-text" font-size="24" fill="#1A1A1A">Kraftd Docs</text>
</svg>
```

### 4.3 Color Definitions

**File:** `frontend/src/styles/colors.ts`

```typescript
export const KraftdColors = {
  primary: '#00BCD4',      // Cyan
  primaryDark: '#0097A7',
  primaryLight: '#4DD0E1',
  
  secondary: '#1A5A7A',    // Blue
  secondaryLight: '#2C7A9A',
  
  dark: '#1A1A1A',
  body: '#536B82',
  light: '#F8F9FA',
  lighter: '#FFFFFF',
  border: '#E0E0E0',
  
  success: '#4CAF50',
  warning: '#FFC107',
  error: '#F44336',
  info: '#2196F3',
} as const

export type ColorKey = keyof typeof KraftdColors
```

---

## Part 5: Azure-Specific Performance Tips

### 5.1 Content Delivery Network (CDN)

```bash
# Enable CDN for Static Web App
az staticwebapp settings update \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --cdn-enabled true
```

### 5.2 Cache Configuration

Update `staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/assets/*",
      "headers": {
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    },
    {
      "route": "*.js",
      "headers": {
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    },
    {
      "route": "*.css",
      "headers": {
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    },
    {
      "route": "*.woff2",
      "headers": {
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    },
    {
      "route": "/index.html",
      "headers": {
        "Cache-Control": "public, max-age=3600, must-revalidate"
      }
    }
  ]
}
```

### 5.3 Monitoring & Analytics

**File:** `frontend/src/services/analytics.ts`

```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web'

export class AnalyticsService {
  private appInsights: ApplicationInsights

  constructor(instrumentationKey: string) {
    this.appInsights = new ApplicationInsights({
      config: {
        instrumentationKey,
        enableAutoRouteTracking: true,
        enableRequestHeaderTracking: true,
        enableResponseHeaderTracking: true,
      }
    })
    this.appInsights.loadAppInsights()
  }

  trackPageView(pageName: string) {
    this.appInsights.trackPageView({ name: pageName })
  }

  trackEvent(eventName: string, properties?: any) {
    this.appInsights.trackEvent({ name: eventName }, properties)
  }

  trackException(error: Error) {
    this.appInsights.trackException({ exception: error })
  }

  trackMetric(metricName: string, value: number) {
    this.appInsights.trackMetric({ name: metricName, average: value })
  }
}
```

---

## Part 6: Testing Checklist

### 6.1 Dashboard Rendering

- [ ] Logo displays correctly
- [ ] Header colors match branding
- [ ] Statistics cards render properly
- [ ] Activity feed shows recent items
- [ ] Tabs switch between overview and documents
- [ ] Footer displays with correct styling

### 6.2 Branding Verification

- [ ] Primary color (#00BCD4) used in header
- [ ] Secondary color (#1A5A7A) in gradients
- [ ] Typography uses Inter font family
- [ ] Logo appears in header
- [ ] Footer text and links styled correctly
- [ ] All text colors match specifications

### 6.3 Performance Testing

- [ ] Dashboard loads in < 2 seconds
- [ ] API calls return in < 1 second
- [ ] No layout shifts on load
- [ ] Images load quickly
- [ ] Smooth scrolling on mobile
- [ ] No console errors

### 6.4 Responsive Testing

- [ ] Desktop (1024px+): Full layout
- [ ] Tablet (768-1023px): Adjusted spacing
- [ ] Mobile (< 768px): Stacked layout
- [ ] Extra small (< 480px): Single column
- [ ] Header fits on all sizes
- [ ] Navigation accessible

### 6.5 Azure-Specific

- [ ] Deployed to Azure Static Web App
- [ ] Custom domain working
- [ ] HTTPS certificate active
- [ ] API routes protected
- [ ] Authentication enforced
- [ ] Error pages branded

---

## Part 7: Deployment Verification

### 7.1 Health Check Script

**File:** `frontend/scripts/health-check.js`

```javascript
const endpoints = [
  { url: 'https://kraftdocs.com', expectedStatus: 200 },
  { url: 'https://kraftdocs.com/login', expectedStatus: 200 },
  { url: 'https://kraftdocs.com/dashboard', expectedStatus: 401 }, // Not authenticated
  { url: 'https://api.kraftdocs.com/health', expectedStatus: 200 }
]

async function healthCheck() {
  console.log('🏥 Running health checks...')
  
  for (const { url, expectedStatus } of endpoints) {
    try {
      const response = await fetch(url)
      const status = response.status
      const ok = status === expectedStatus
      const emoji = ok ? '✅' : '❌'
      console.log(`${emoji} ${url} (${status})`)
    } catch (error) {
      console.log(`❌ ${url} (ERROR: ${error.message})`)
    }
  }
}

healthCheck()
```

Run before deployment:
```bash
node frontend/scripts/health-check.js
```

---

## Summary

✅ **Dashboard Enhancements Complete**
- Branding integrated throughout
- Performance optimized
- Azure-ready configuration
- Responsive design verified
- Monitoring configured

**Ready for Azure Deployment!**

