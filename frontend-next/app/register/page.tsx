/**
 * Register Page - Complete user registration form
 *
 * Features:
 * - Email and password registration
 * - Password strength validation
 * - Password confirmation
 * - Terms and privacy acceptance
 * - Form validation with error messages
 * - Loading states during registration
 * - Responsive design with Tailwind
 * - Link to login page
 */

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '../../hooks/useAuth'

interface FormErrors {
  email?: string
  firstName?: string
  lastName?: string
  password?: string
  confirmPassword?: string
  terms?: string
  general?: string
}

export default function RegisterPage() {
  const { register, isAuthenticating, error: authError } = useAuth()

  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
    acceptPrivacy: false,
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [showPassword, setShowPassword] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong' | null>(null)

  // Check password strength
  const checkPasswordStrength = (password: string): 'weak' | 'medium' | 'strong' => {
    if (!password) return 'weak'

    let strength = 0
    if (password.length >= 8) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[a-z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[!@#$%^&*()-_=+\[\]{}|;:'",.<>?/]/.test(password)) strength++

    if (strength <= 2) return 'weak'
    if (strength === 3) return 'medium'
    return 'strong'
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    // Name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required'
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else {
      const strength = checkPasswordStrength(formData.password)
      if (strength === 'weak') {
        newErrors.password =
          'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
      }
    }

    // Confirm password
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    // Terms acceptance
    if (!formData.acceptTerms) {
      newErrors.terms = 'You must accept the terms of service'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Simple email validation
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Validate
    if (!validateForm()) {
      return
    }

    // Submit registration
    const result = await register({
      email: formData.email,
      password: formData.password,
      firstName: formData.firstName,
      lastName: formData.lastName,
      acceptTerms: formData.acceptTerms,
      acceptPrivacy: formData.acceptPrivacy,
    })

    if (!result.success) {
      setErrors({ general: result.error })
    }
    // On success, useAuth hook redirects to dashboard
  }

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target
    const newValue = type === 'checkbox' ? checked : value

    setFormData(prev => ({ ...prev, [name]: newValue }))

    // Clear error for this field when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }

    // Update password strength
    if (name === 'password') {
      setPasswordStrength(checkPasswordStrength(value))
    }
  }

  const passwordStrengthColor = {
    weak: 'bg-red-500',
    medium: 'bg-yellow-500',
    strong: 'bg-green-500',
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8">
            <div className="flex items-center justify-center mb-2">
              <div className="text-4xl font-bold text-white">K</div>
            </div>
            <h1 className="text-2xl font-bold text-white text-center">
              KRAFTD
            </h1>
            <p className="text-blue-100 text-sm text-center mt-2">
              Create Your Account
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-6 py-8 space-y-4">
            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                disabled={isAuthenticating}
                placeholder="you@example.com"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  errors.email
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-300 dark:border-slate-600 focus:ring-blue-500'
                } disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-500 dark:disabled:text-slate-400 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500`}
              />
              {errors.email && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{errors.email}</p>
              )}
            </div>

            {/* First Name */}
            <div>
              <label
                htmlFor="firstName"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
              >
                First Name
              </label>
              <input
                id="firstName"
                type="text"
                name="firstName"
                value={formData.firstName}
                onChange={handleInputChange}
                disabled={isAuthenticating}
                placeholder="John"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  errors.firstName
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-300 dark:border-slate-600 focus:ring-blue-500'
                } disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-500 dark:disabled:text-slate-400 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500`}
              />
              {errors.firstName && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{errors.firstName}</p>
              )}
            </div>

            {/* Last Name */}
            <div>
              <label
                htmlFor="lastName"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
              >
                Last Name
              </label>
              <input
                id="lastName"
                type="text"
                name="lastName"
                value={formData.lastName}
                onChange={handleInputChange}
                disabled={isAuthenticating}
                placeholder="Doe"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  errors.lastName
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-300 dark:border-slate-600 focus:ring-blue-500'
                } disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-500 dark:disabled:text-slate-400 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500`}
              />
              {errors.lastName && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{errors.lastName}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  disabled={isAuthenticating}
                  placeholder="••••••••"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition ${
                    errors.password
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-slate-300 dark:border-slate-600 focus:ring-blue-500'
                  } disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-500 dark:disabled:text-slate-400 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                  disabled={isAuthenticating}
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-4.803m5.596-3.856a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Password Strength Indicator */}
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex-1 h-1 bg-slate-200 dark:bg-slate-700 rounded overflow-hidden">
                      <div
                        className={`h-full transition-all ${passwordStrengthColor[passwordStrength || 'weak']}`}
                        style={{
                          width: passwordStrength === 'weak' ? '33%' : passwordStrength === 'medium' ? '66%' : '100%',
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                      {passwordStrength === 'weak' && '❌ Weak'}
                      {passwordStrength === 'medium' && '⚠️ Medium'}
                      {passwordStrength === 'strong' && '✅ Strong'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    • 8+ characters • Uppercase & lowercase • Number • Special character
                  </p>
                </div>
              )}

              {errors.password && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                disabled={isAuthenticating}
                placeholder="••••••••"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  errors.confirmPassword
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-300 dark:border-slate-600 focus:ring-blue-500'
                } disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-500 dark:disabled:text-slate-400 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500`}
              />
              {errors.confirmPassword && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Terms Acceptance */}
            <div className="space-y-2">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  name="acceptTerms"
                  checked={formData.acceptTerms}
                  onChange={handleInputChange}
                  disabled={isAuthenticating}
                  className="mt-1 rounded"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  I agree to the{' '}
                  <a href="#" className="text-blue-600 dark:text-blue-400 hover:underline">
                    Terms of Service
                  </a>
                </span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  name="acceptPrivacy"
                  checked={formData.acceptPrivacy}
                  onChange={handleInputChange}
                  disabled={isAuthenticating}
                  className="mt-1 rounded"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  I agree to the{' '}
                  <a href="#" className="text-blue-600 dark:text-blue-400 hover:underline">
                    Privacy Policy
                  </a>
                </span>
              </label>

              {errors.terms && (
                <p className="text-red-500 dark:text-red-400 text-sm">{errors.terms}</p>
              )}
            </div>

            {/* General Error */}
            {(authError || errors.general) && (
              <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <p className="text-red-700 dark:text-red-300 text-sm">{authError || errors.general}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold py-2.5 px-4 rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 dark:focus:ring-offset-slate-900"
            >
              {isAuthenticating ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Creating Account...
                </>
              ) : (
                'Create Account'
              )}
            </button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-300 dark:border-slate-600"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400">Already have an account?</span>
              </div>
            </div>

            {/* Login Link */}
            <Link
              href="/login"
              className="block w-full text-center border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold py-2 px-4 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition dark:focus:ring-offset-slate-900"
            >
              Sign In
            </Link>
          </form>
        </div>
      </div>
    </div>
  )
}
