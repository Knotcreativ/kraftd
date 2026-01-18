import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import '../pages/VerifyEmail.css'

export default function VerifyEmail() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { api } = useAuth()
  
  const [token, setToken] = useState('')
  const [manualToken, setManualToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  // Auto-detect token from URL on mount
  useEffect(() => {
    const urlToken = searchParams.get('token')
    if (urlToken) {
      setToken(urlToken)
      setLoading(true)
      handleVerification(urlToken)
    }
  }, [searchParams])

  const handleVerification = async (verificationToken: string) => {
    try {
      setError('')
      setMessage('Verifying your email...')
      
      const response = await api.verifyEmail(verificationToken)
      
      setSuccess(true)
      setMessage(response.message || 'Email verified successfully!')
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: any) {
      setSuccess(false)
      const errorMsg = err.response?.data?.detail?.message || 
                       err.response?.data?.detail ||
                       'Failed to verify email. Please try again.'
      setError(errorMsg)
      setMessage('')
    } finally {
      setLoading(false)
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!manualToken.trim()) {
      setError('Please enter a verification token')
      return
    }
    
    setLoading(true)
    await handleVerification(manualToken)
  }

  // If token was auto-detected and processing
  if (token && loading) {
    return (
      <div className="verify-container">
        <div className="verify-card">
          <div className="loading-spinner"></div>
          <h2>Verifying Your Email</h2>
          <p>{message}</p>
        </div>
      </div>
    )
  }

  // Success state
  if (success) {
    return (
      <div className="verify-container">
        <div className="verify-card success">
          <div className="success-checkmark">✓</div>
          <h2>Email Verified!</h2>
          <p>{message}</p>
          <p className="redirect-notice">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  // Error state with option to paste token
  return (
    <div className="verify-container">
      <div className="verify-card">
        <h1>Verify Your Email</h1>
        
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        <p className="verify-description">
          Enter the verification token from your email to verify your account.
        </p>
        
        <form onSubmit={handleManualSubmit}>
          <div className="form-group">
            <label htmlFor="token">Verification Token</label>
            <input
              id="token"
              type="text"
              value={manualToken}
              onChange={(e) => setManualToken(e.target.value)}
              placeholder="Paste your verification token here"
              disabled={loading}
              className="token-input"
            />
            <p className="token-hint">
              The token is in the verification link sent to your email.
            </p>
          </div>
          
          <button
            type="submit"
            disabled={loading || !manualToken.trim()}
            className="verify-button"
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>
        
        <div className="divider">or</div>
        
        <p className="check-email-text">
          Check your email for a verification link and click it directly.
        </p>
        
        <div className="back-to-login">
          <p>Already verified?</p>
          <button
            onClick={() => navigate('/login')}
            className="link-button"
          >
            Go to Login
          </button>
        </div>
      </div>
    </div>
  )
}
