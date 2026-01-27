import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import VerifyEmail from './pages/VerifyEmail'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import TermsOfService from './pages/TermsOfService'
import PrivacyPolicy from './pages/PrivacyPolicy'
import Layout from './components/Layout'
import DocumentReviewDetail from './components/DocumentReviewDetail'
import { StreamingDashboard } from './pages/StreamingDashboard'
import { AnalyticsDashboard } from './pages/AnalyticsDashboard'
import DashboardPreview from './components/DashboardPreview'
import AlertPreferences from './components/AlertPreferences'
import ErrorBoundary from './components/ErrorBoundary'
import AnalyticsPage from './pages/AnalyticsPage'
import PreferencesPage from './pages/PreferencesPage'
import { apiClient } from './services/api'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function AppContent() {
  useEffect(() => {
    // PHASE 8: Get CSRF token on app load
    const initializeCsrfToken = async () => {
      try {
        await apiClient.getCsrfToken()
      } catch (error) {
        console.error('Failed to initialize CSRF token:', error)
      }
    }
    initializeCsrfToken()
  }, [])


  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/review/:documentId"
          element={
            <ProtectedRoute>
              <Layout>
                <DocumentReviewDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/streaming-dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <StreamingDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Layout>
                <AnalyticsPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/custom"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardPreview />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/preferences"
          element={
            <ProtectedRoute>
              <Layout>
                <PreferencesPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/preferences/alerts"
          element={
            <ProtectedRoute>
              <Layout>
                <PreferencesPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard-builder"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardPreview />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/alert-preferences"
          element={
            <ProtectedRoute>
              <Layout>
                <AlertPreferences />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
