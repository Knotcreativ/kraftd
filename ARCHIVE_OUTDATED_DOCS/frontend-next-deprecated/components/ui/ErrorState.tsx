'use client'

import React from 'react'
import clsx from 'clsx'

interface ErrorStateProps {
  icon?: React.ReactNode
  title?: string
  message: string
  action?: React.ReactNode
  className?: string
}

const ErrorState = React.forwardRef<HTMLDivElement, ErrorStateProps>(
  (
    {
      icon,
      title = 'Something went wrong',
      message,
      action,
      className,
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex flex-col items-center justify-center gap-4 rounded-lg border border-red-200 bg-red-50 py-8 px-6',
          className
        )}
      >
        {icon ? (
          <div className="text-4xl">{icon}</div>
        ) : (
          <div className="text-5xl">⚠️</div>
        )}

        <div className="flex flex-col items-center gap-2">
          <h3 className="text-lg font-semibold text-red-900">{title}</h3>
          <p className="max-w-sm text-center text-red-800">{message}</p>
        </div>

        {action && (
          <div className="mt-2">
            {action}
          </div>
        )}
      </div>
    )
  }
)

ErrorState.displayName = 'ErrorState'
export default ErrorState
