'use client'

import React from 'react'
import { clsx } from 'clsx'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circle' | 'rectangle'
  count?: number
  height?: string
  width?: string
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  (
    {
      variant = 'rectangle',
      count = 1,
      height = 'h-4',
      width = 'w-full',
      className,
      ...props
    },
    ref
  ) => {
    const skeletons = Array.from({ length: count })

    const variantClasses = {
      text: 'rounded',
      circle: 'rounded-full',
      rectangle: 'rounded-lg',
    }

    return (
      <div className={className} ref={ref} {...props}>
        {skeletons.map((_, i) => (
          <div
            key={i}
            className={clsx(
              'bg-gray-200 animate-pulse',
              variantClasses[variant],
              height,
              width,
              i < count - 1 && 'mb-2'
            )}
          />
        ))}
      </div>
    )
  }
)

Skeleton.displayName = 'Skeleton'

/**
 * Skeleton Loader for Cards
 */
export const CardSkeleton = () => (
  <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
    <Skeleton height="h-6" width="w-1/3" />
    <Skeleton count={3} height="h-4" />
    <div className="flex gap-2 pt-4">
      <Skeleton height="h-8" width="w-20" variant="rectangle" />
      <Skeleton height="h-8" width="w-20" variant="rectangle" />
    </div>
  </div>
)

CardSkeleton.displayName = 'CardSkeleton'

/**
 * Skeleton Loader for List Items
 */
export const ListItemSkeleton = () => (
  <div className="flex items-center gap-4 p-4 border-b border-gray-200">
    <Skeleton variant="circle" height="h-10" width="w-10" />
    <div className="flex-1 space-y-2">
      <Skeleton height="h-4" width="w-2/3" />
      <Skeleton height="h-3" width="w-1/2" />
    </div>
    <Skeleton height="h-8" width="w-16" />
  </div>
)

ListItemSkeleton.displayName = 'ListItemSkeleton'

/**
 * Skeleton Loader for Page
 */
export const PageSkeleton = () => (
  <div className="space-y-6">
    <div>
      <Skeleton height="h-8" width="w-1/3" />
      <Skeleton height="h-4" width="w-1/2" className="mt-2" />
    </div>
    <div className="grid gap-6 md:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  </div>
)

PageSkeleton.displayName = 'PageSkeleton'
