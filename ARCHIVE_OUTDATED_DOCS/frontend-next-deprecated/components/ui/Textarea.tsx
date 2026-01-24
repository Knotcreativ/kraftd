'use client'

import React from 'react'
import clsx from 'clsx'

export type TextareaSize = 'sm' | 'md' | 'lg'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  helperText?: string
  error?: boolean
  errorMessage?: string
  size?: TextareaSize
  required?: boolean
  characterCount?: boolean
}

const sizeStyles: Record<TextareaSize, string> = {
  sm: 'px-2.5 py-1.5 text-sm',
  md: 'px-3 py-2 text-base',
  lg: 'px-4 py-3 text-lg',
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      helperText,
      error = false,
      errorMessage,
      size = 'md',
      required = false,
      className,
      disabled,
      id,
      maxLength,
      characterCount = false,
      ...props
    },
    ref
  ) => {
    const [charCount, setCharCount] = React.useState(0)
    const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className={clsx('flex flex-col gap-1.5', className)}>
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
            {required && <span className="ml-1 text-red-500">*</span>}
          </label>
        )}

        <textarea
          ref={ref}
          id={inputId}
          disabled={disabled}
          maxLength={maxLength}
          onChange={(e) => {
            setCharCount(e.currentTarget.value.length)
            props.onChange?.(e)
          }}
          className={clsx(
            'w-full rounded-lg border font-medium transition-all duration-200 resize-none',
            'focus:outline-none focus:ring-2 focus:ring-offset-2',
            'disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500 dark:disabled:bg-gray-800 dark:disabled:text-gray-400',
            sizeStyles[size],
            error
              ? 'border-red-500 bg-red-50 text-red-900 focus:border-red-500 focus:ring-red-500 dark:bg-red-950 dark:text-red-200'
              : 'border-gray-300 bg-white text-gray-900 placeholder-gray-400 hover:border-gray-400 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500 dark:hover:border-gray-500 dark:focus:ring-offset-gray-950'
          )}
          {...props}
        />

        <div className="flex items-center justify-between gap-2">
          <div>
            {error && errorMessage && (
              <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
            )}
            {!error && helperText && (
              <p className="text-sm text-gray-500 dark:text-gray-400">{helperText}</p>
            )}
          </div>

          {characterCount && maxLength && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {charCount} / {maxLength}
            </p>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
export default Textarea
