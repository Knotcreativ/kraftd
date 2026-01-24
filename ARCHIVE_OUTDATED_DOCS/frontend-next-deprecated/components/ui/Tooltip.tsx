'use client'

import React from 'react'
import clsx from 'clsx'

interface TooltipProps {
  content: string
  children: React.ReactNode
  position?: 'top' | 'right' | 'bottom' | 'left'
  delay?: number
  className?: string
}

const positionStyles = {
  top: 'bottom-full mb-2 -translate-x-1/2 left-1/2',
  right: 'left-full ml-2 top-1/2 -translate-y-1/2',
  bottom: 'top-full mt-2 -translate-x-1/2 left-1/2',
  left: 'right-full mr-2 top-1/2 -translate-y-1/2',
}

const arrowStyles = {
  top: 'bottom-[-4px] left-1/2 -translate-x-1/2 border-t-gray-900 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent',
  right: 'left-[-4px] top-1/2 -translate-y-1/2 border-r-gray-900 border-t-4 border-b-4 border-r-4 border-t-transparent border-b-transparent',
  bottom: 'top-[-4px] left-1/2 -translate-x-1/2 border-b-gray-900 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent',
  left: 'right-[-4px] top-1/2 -translate-y-1/2 border-l-gray-900 border-t-4 border-b-4 border-l-4 border-t-transparent border-b-transparent',
}

const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  (
    {
      content,
      children,
      position = 'top',
      delay = 200,
      className,
    },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(false)
    const timeoutRef = React.useRef<NodeJS.Timeout>()

    const handleMouseEnter = () => {
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true)
      }, delay)
    }

    const handleMouseLeave = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      setIsVisible(false)
    }

    React.useEffect(() => {
      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }
      }
    }, [])

    return (
      <div
        ref={ref}
        className="relative inline-flex"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}

        {isVisible && (
          <div
            className={clsx(
              'pointer-events-none absolute z-50 whitespace-nowrap',
              'rounded-md bg-gray-900 px-2 py-1 text-sm text-white',
              'animate-fade-in',
              positionStyles[position],
              className
            )}
            role="tooltip"
          >
            {content}
            <div
              className={clsx(
                'absolute h-0 w-0',
                arrowStyles[position]
              )}
            />
          </div>
        )}
      </div>
    )
  }
)

Tooltip.displayName = 'Tooltip'
export default Tooltip
