'use client'

import React from 'react'
import clsx from 'clsx'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      icon,
      title,
      description,
      action,
      className,
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex flex-col items-center justify-center gap-4 py-12 px-6',
          className
        )}
      >
        {icon && (
          <div className="text-5xl text-gray-400">
            {icon}
          </div>
        )}

        <div className="flex flex-col items-center gap-2">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {description && (
            <p className="max-w-sm text-center text-gray-600">{description}</p>
          )}
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

EmptyState.displayName = 'EmptyState'
export default EmptyState
