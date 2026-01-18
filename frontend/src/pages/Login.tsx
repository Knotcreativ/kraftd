import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (isRegister && (!acceptedTerms || !acceptedPrivacy)) {
      setError('Please accept the Terms of Service and Privacy Policy to continue')
      return
    }

    setIsLoading(true)

    try {
      if (isRegister) {
        await register(email, password, acceptedTerms, acceptedPrivacy, name || undefined)
      } else {
        await login(email, password)
      }
      navigate('/dashboard')
    } catch (error) {
      const message = error instanceof Error ? error.message : (isRegister ? 'Registration failed' : 'Login failed')
      setError(message)
      console.error(isRegister ? 'Registration failed' : 'Login failed', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleMode = () => {
    setIsRegister(!isRegister)
    setError(null)
    setEmail('')
    setPassword('')
    setName('')
    setAcceptedTerms(false)
    setAcceptedPrivacy(false)
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>KraftdIntel</h1>
          <p>Intelligent Procurement Management</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <h2>{isRegister ? 'Create Account' : 'Sign In'}</h2>

          {error && (
            <div className="form-error">
              <p>{error}</p>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={isLoading}
            />
            {isRegister && <p className="form-hint">Password must be 8-128 characters, no spaces</p>}
          </div>

          {isRegister && (
            <>
              <div className="form-group">
                <label htmlFor="name">Full Name (Optional)</label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your Name"
                  disabled={isLoading}
                />
              </div>

              <div className="form-group checkbox-group">
                <input
                  id="terms"
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  disabled={isLoading}
                />
                <label htmlFor="terms" className="checkbox-label">
                  I agree to the{' '}
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => navigate('/terms-of-service')}
                  >
                    Terms of Service
                  </button>
                </label>
              </div>

              <div className="form-group checkbox-group">
                <input
                  id="privacy"
                  type="checkbox"
                  checked={acceptedPrivacy}
                  onChange={(e) => setAcceptedPrivacy(e.target.checked)}
                  disabled={isLoading}
                />
                <label htmlFor="privacy" className="checkbox-label">
                  I agree to the{' '}
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => navigate('/privacy-policy')}
                  >
                    Privacy Policy
                  </button>
                </label>
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || (isRegister && (!acceptedTerms || !acceptedPrivacy))}
          >
            {isLoading ? 'Processing...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>

          <button
            type="button"
            className="btn-link"
            onClick={handleToggleMode}
            disabled={isLoading}
          >
            {isRegister ? 'Already have an account? Sign In' : 'Need an account? Register'}
          </button>
        </form>

        <div className="login-footer">
          <p>Secure. Efficient. Intelligent.</p>
        </div>
      </div>
    </div>
  )
}
