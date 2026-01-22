'use client'

import React from 'react'
import clsx from 'clsx'

interface DividerProps {
  className?: string
  orientation?: 'horizontal' | 'vertical'
  label?: string
  variant?: 'solid' | 'dashed' | 'dotted'
  color?: 'light' | 'default' | 'dark'
}

const colorStyles = {
  light: 'border-gray-200',
  default: 'border-gray-300',
  dark: 'border-gray-400',
}

const variantStyles = {
  solid: 'border-solid',
  dashed: 'border-dashed',
  dotted: 'border-dotted',
}

const Divider = React.forwardRef<HTMLDivElement, DividerProps>(
  (
    {
      className,
      orientation = 'horizontal',
      label,
      variant = 'solid',
      color = 'default',
    },
    ref
  ) => {
    const isHorizontal = orientation === 'horizontal'

    if (label && isHorizontal) {
      return (
        <div
          ref={ref}
          className={clsx('relative flex items-center gap-3', className)}
        >
          <div
            className={clsx(
              'flex-1 border-t',
              variantStyles[variant],
              colorStyles[color]
            )}
          />
          <span className="text-sm font-medium text-gray-600">{label}</span>
          <div
            className={clsx(
              'flex-1 border-t',
              variantStyles[variant],
              colorStyles[color]
            )}
          />
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className={clsx(
          isHorizontal ? 'border-t' : 'border-l',
          variantStyles[variant],
          colorStyles[color],
          className
        )}
      />
    )
  }
)

Divider.displayName = 'Divider'
export default Divider
