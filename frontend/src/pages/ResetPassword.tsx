import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { apiClient } from '../services/api'
import './ResetPassword.css'

function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong'>('weak')
  const [showPassword, setShowPassword] = useState(false)

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.')
    }
  }, [token])

  // Check password strength
  useEffect(() => {
    if (newPassword.length >= 8) {
      if (newPassword.length >= 12 && /[A-Z]/.test(newPassword) && /[0-9]/.test(newPassword)) {
        setPasswordStrength('strong')
      } else if (newPassword.length >= 10) {
        setPasswordStrength('medium')
      } else {
        setPasswordStrength('weak')
      }
    } else {
      setPasswordStrength('weak')
    }
  }, [newPassword])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    // Validate inputs
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.')
      setIsLoading(false)
      return
    }

    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields.')
      setIsLoading(false)
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      setIsLoading(false)
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      setIsLoading(false)
      return
    }

    try {
      const response = await apiClient.resetPassword(token, newPassword, confirmPassword)
      
      if (response.status === 'success') {
        setSuccess(true)
        // Auto-redirect to login after 4 seconds
        setTimeout(() => {
          navigate('/login')
        }, 4000)
      } else {
        setError(response.message || 'Failed to reset password')
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reset password'
      setError(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="reset-password-container">
        <div className="reset-password-card">
          <div className="success-state">
            <div className="success-icon">✓</div>
            <h2>Password Changed!</h2>
            <p className="success-message">
              Your password has been successfully reset.
            </p>
            <p className="success-hint">
              You can now log in with your new password.
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
    <div className="reset-password-container">
      <div className="reset-password-card">
        <h1>Reset Your Password</h1>
        <p className="form-description">
          Enter your new password below.
        </p>

        {error && (
          <div className="form-error">
            <span>⚠️</span> {error}
          </div>
        )}

        {!token && (
          <div className="invalid-token">
            <p>Invalid or expired reset link.</p>
            <Link to="/forgot-password" className="request-new-link">
              Request a new password reset
            </Link>
          </div>
        )}

        {token && (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="newPassword"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {newPassword && (
                <div className={`strength-indicator strength-${passwordStrength}`}>
                  <div className="strength-bar">
                    <div className="strength-fill"></div>
                  </div>
                  <span className="strength-text">
                    {passwordStrength === 'strong' ? '💪 Strong' : 
                     passwordStrength === 'medium' ? '👍 Medium' : 
                     '⚠️ Weak'}
                  </span>
                </div>
              )}
              <div className="password-hint">
                • 8-128 characters
                • No spaces allowed
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                disabled={isLoading}
              />
            </div>

            {newPassword && confirmPassword && newPassword !== confirmPassword && (
              <div className="password-mismatch">
                ⚠️ Passwords do not match
              </div>
            )}

            <button 
              type="submit" 
              disabled={isLoading || !newPassword || !confirmPassword || newPassword !== confirmPassword}
              className="submit-btn"
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}

        <div className="form-divider">or</div>

        <Link to="/login" className="back-to-login">
          ← Back to Login
        </Link>
      </div>
    </div>
  )
}

export default ResetPassword
