'use client'

import React from 'react'
import clsx from 'clsx'

interface SectionHeaderProps {
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
  level?: 'h2' | 'h3' | 'h4'
}

const levelStyles = {
  h2: 'text-2xl',
  h3: 'text-xl',
  h4: 'text-lg',
}

const SectionHeader = React.forwardRef<HTMLDivElement, SectionHeaderProps>(
  (
    {
      title,
      description,
      action,
      className,
      level = 'h2',
    },
    ref
  ) => {
    const HeadingTag = level

    return (
      <div
        ref={ref}
        className={clsx(
          'flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between',
          className
        )}
      >
        <div className="flex flex-col gap-1">
          <HeadingTag
            className={clsx('font-bold text-gray-900', levelStyles[level])}
          >
            {title}
          </HeadingTag>
          {description && (
            <p className="text-sm text-gray-600">{description}</p>
          )}
        </div>
        {action && <div className="flex items-center gap-2">{action}</div>}
      </div>
    )
  }
)

SectionHeader.displayName = 'SectionHeader'
export default SectionHeader
