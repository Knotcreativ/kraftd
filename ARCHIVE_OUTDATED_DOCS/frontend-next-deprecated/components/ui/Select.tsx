'use client'

import React from 'react'
import clsx from 'clsx'

export type SelectSize = 'sm' | 'md' | 'lg'

export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string
  helperText?: string
  error?: boolean
  errorMessage?: string
  size?: SelectSize
  options: SelectOption[]
  required?: boolean
  leftIcon?: React.ReactNode
}

const sizeStyles: Record<SelectSize, string> = {
  sm: 'px-2.5 py-1.5 text-sm h-8',
  md: 'px-3 py-2 text-base h-10',
  lg: 'px-4 py-3 text-lg h-12',
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      helperText,
      error = false,
      errorMessage,
      size = 'md',
      options,
      required = false,
      leftIcon,
      className,
      disabled,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `select-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
            {required && <span className="ml-1 text-red-500">*</span>}
          </label>
        )}

        <div className={clsx('relative', className)}>
          {leftIcon && (
            <div className="pointer-events-none absolute left-3 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center text-gray-400 dark:text-gray-500">
              {leftIcon}
            </div>
          )}

          <select
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={clsx(
              'w-full appearance-none rounded-lg border font-medium transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500 dark:disabled:bg-gray-800 dark:disabled:text-gray-400',
              sizeStyles[size],
              leftIcon && 'pl-9',
              error
                ? 'border-red-500 bg-red-50 text-red-900 focus:border-red-500 focus:ring-red-500 dark:bg-red-950 dark:text-red-200'
                : 'border-gray-300 bg-white text-gray-900 hover:border-gray-400 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:hover:border-gray-500 dark:focus:ring-offset-gray-950'
            )}
            {...props}
          >
            <option value="">Select an option</option>
            {options.map((option) => (
              <option
                key={`${option.value}`}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>

          {/* Chevron Icon */}
          <div className="pointer-events-none absolute right-3 top-1/2 flex h-4 w-4 -translate-y-1/2 items-center justify-center text-gray-400 dark:text-gray-500">
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
            </svg>
          </div>
        </div>

        {error && errorMessage && (
          <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
        )}
        {!error && helperText && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{helperText}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'
export default Select
