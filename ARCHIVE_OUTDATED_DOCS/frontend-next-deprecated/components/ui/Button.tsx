'use client'

import React, { forwardRef } from 'react'
import { clsx } from 'clsx'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-600 text-white hover:bg-primary-700 dark:bg-primary-600 dark:hover:bg-primary-500 focus:ring-primary-500 active:bg-primary-800 dark:active:bg-primary-700 disabled:bg-primary-400 dark:disabled:bg-primary-700 dark:focus:ring-offset-gray-950',
  secondary:
    'bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600 focus:ring-gray-500 active:bg-gray-400 dark:active:bg-gray-800 disabled:bg-gray-100 dark:disabled:bg-gray-800 dark:focus:ring-offset-gray-950',
  outline:
    'border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 focus:ring-gray-500 active:bg-gray-100 dark:active:bg-gray-900 disabled:border-gray-200 dark:disabled:border-gray-700 disabled:text-gray-400 dark:disabled:text-gray-600 dark:focus:ring-offset-gray-950',
  ghost:
    'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:ring-gray-500 active:bg-gray-200 dark:active:bg-gray-900 disabled:text-gray-400 dark:disabled:text-gray-600 dark:focus:ring-offset-gray-950',
  danger:
    'bg-danger-600 text-white hover:bg-danger-700 dark:bg-danger-600 dark:hover:bg-danger-500 focus:ring-danger-500 active:bg-danger-800 dark:active:bg-danger-700 disabled:bg-danger-400 dark:disabled:bg-danger-700 dark:focus:ring-offset-gray-950',
  success:
    'bg-success-600 text-white hover:bg-success-700 dark:bg-success-600 dark:hover:bg-success-500 focus:ring-success-500 active:bg-success-800 dark:active:bg-success-700 disabled:bg-success-400 dark:disabled:bg-success-700 dark:focus:ring-offset-gray-950',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm font-medium h-8',
  md: 'px-4 py-2 text-base font-semibold h-10',
  lg: 'px-6 py-3 text-lg font-semibold h-12',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled = false,
      children,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={clsx(
          // Base styles
          'inline-flex items-center justify-center rounded-lg font-semibold',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-950',
          'disabled:cursor-not-allowed disabled:opacity-60',
          'active:scale-95',
          // Variant styles
          variantStyles[variant],
          // Size styles
          sizeStyles[size],
          // Full width
          fullWidth && 'w-full',
          // Custom className
          className
        )}
        {...props}
      >
        {isLoading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!isLoading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!isLoading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
