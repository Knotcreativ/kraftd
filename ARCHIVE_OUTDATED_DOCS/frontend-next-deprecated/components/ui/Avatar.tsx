'use client'

import React from 'react'
import clsx from 'clsx'

export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

interface AvatarProps {
  src?: string
  alt?: string
  initials?: string
  size?: AvatarSize
  className?: string
  backgroundColor?: string
  online?: boolean
}

const sizeStyles: Record<AvatarSize, { container: string; text: string }> = {
  xs: { container: 'h-6 w-6', text: 'text-xs' },
  sm: { container: 'h-8 w-8', text: 'text-sm' },
  md: { container: 'h-10 w-10', text: 'text-base' },
  lg: { container: 'h-12 w-12', text: 'text-lg' },
  xl: { container: 'h-16 w-16', text: 'text-2xl' },
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  (
    {
      src,
      alt = 'Avatar',
      initials = '?',
      size = 'md',
      className,
      backgroundColor = 'bg-primary-500',
      online,
    },
    ref
  ) => {
    const styles = sizeStyles[size]

    return (
      <div
        ref={ref}
        className={clsx(
          'relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold text-white',
          styles.container,
          backgroundColor,
          className
        )}
      >
        {src ? (
          <img
            src={src}
            alt={alt}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className={styles.text}>{initials}</span>
        )}

        {online !== undefined && (
          <div
            className={clsx(
              'absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white',
              online ? 'bg-green-500' : 'bg-gray-400'
            )}
            aria-label={online ? 'Online' : 'Offline'}
          />
        )}
      </div>
    )
  }
)

Avatar.displayName = 'Avatar'
export default Avatar
