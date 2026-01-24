'use client'

import React, { useEffect, useRef } from 'react'
import { clsx } from 'clsx'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
  closeOnBackdropClick?: boolean
  closeOnEscape?: boolean
}

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
}

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnBackdropClick = true,
  closeOnEscape = true,
}: ModalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null)
    const modalRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
      const handleEscape = (e: KeyboardEvent) => {
        if (closeOnEscape && e.key === 'Escape') {
          onClose()
        }
      }

      if (isOpen) {
        window.addEventListener('keydown', handleEscape)
        document.body.style.overflow = 'hidden'
        // Focus trap: move focus to modal
        modalRef.current?.focus()
      }

      return () => {
        window.removeEventListener('keydown', handleEscape)
        document.body.style.overflow = 'unset'
      }
    }, [isOpen, closeOnEscape, onClose])

    if (!isOpen) return null

    return (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity duration-200 animate-in fade-in-0"
          onClick={() => closeOnBackdropClick && onClose()}
          role="presentation"
        />

        {/* Modal */}
        <div
          ref={dialogRef}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div
            ref={modalRef}
            className={clsx(
              'w-full bg-white dark:bg-gray-900 rounded-lg shadow-xl dark:shadow-2xl',
              'transform transition-all duration-200',
              'animate-in fade-in-0 zoom-in-95',
              sizeStyles[size]
            )}
            tabIndex={-1}
          >
            {/* Header */}
            {title && (
              <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                <h2 id="modal-title" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {title}
                </h2>
                <button
                  onClick={onClose}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 rounded p-1 transition-colors duration-200"
                  aria-label="Close modal"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            )}

            {/* Content */}
            <div className="px-6 py-4">{children}</div>

            {/* Footer */}
            {footer && (
              <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-2">
                {footer}
              </div>
            )}
          </div>
        </div>
      </>
    )
}

Modal.displayName = 'Modal'
