import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiClient } from '../services/api'
import './ForgotPassword.css'

function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const response = await apiClient.forgotPassword(email)
      
      if (response.status === 'success') {
        setSuccess(true)
        // Auto-redirect to login after 4 seconds
        setTimeout(() => {
          navigate('/login')
        }, 4000)
      } else {
        setError(response.message || 'Failed to send reset email')
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to send reset email'
      setError(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="forgot-password-container">
        <div className="forgot-password-card">
          <div className="success-state">
            <div className="success-icon">✉️</div>
            <h2>Check Your Email!</h2>
            <p className="success-message">
              If an account exists with this email, you'll receive a password reset link.
            </p>
            <p className="success-hint">
              Please check your email (including spam folder) for the reset link. The link will expire in 24 hours.
            </p>
            <div className="redirect-notice">
              Redirecting to login in a few seconds...
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="forgot-password-container">
      <div className="forgot-password-card">
        <h1>Forgot Password?</h1>
        <p className="form-description">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        {error && (
          <div className="form-error">
            <span>⚠️</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              disabled={isLoading}
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading || !email}
            className="submit-btn"
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <div className="form-divider">or</div>

        <Link to="/login" className="back-to-login">
          ← Back to Login
        </Link>
      </div>
    </div>
  )
}

export default ForgotPassword
