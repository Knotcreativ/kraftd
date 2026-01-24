'use client'

import React from 'react'
import clsx from 'clsx'

interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  layout?: 'vertical' | 'horizontal' | 'inline'
  children: React.ReactNode
}

const Form = React.forwardRef<HTMLFormElement, FormProps>(
  ({ layout = 'vertical', className, children, ...props }, ref) => {
    return (
      <form
        ref={ref}
        className={clsx(
          layout === 'vertical' && 'flex flex-col gap-6',
          layout === 'horizontal' && 'flex flex-col gap-4',
          layout === 'inline' && 'flex flex-wrap items-center gap-4',
          className
        )}
        {...props}
      >
        {children}
      </form>
    )
  }
)

Form.displayName = 'Form'

interface FormGroupProps {
  children: React.ReactNode
  className?: string
  columns?: 1 | 2 | 3
}

const FormGroup = React.forwardRef<HTMLDivElement, FormGroupProps>(
  ({ children, className, columns = 1 }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'grid gap-4',
          columns === 1 && 'grid-cols-1',
          columns === 2 && 'grid-cols-1 sm:grid-cols-2',
          columns === 3 && 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
          className
        )}
      >
        {children}
      </div>
    )
  }
)

FormGroup.displayName = 'FormGroup'

interface FormRowProps {
  children: React.ReactNode
  className?: string
}

const FormRow = React.forwardRef<HTMLDivElement, FormRowProps>(
  ({ children, className }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('flex flex-col gap-4 sm:flex-row sm:gap-6', className)}
      >
        {children}
      </div>
    )
  }
)

FormRow.displayName = 'FormRow'

interface FormFieldProps {
  children: React.ReactNode
  className?: string
  flex?: boolean
}

const FormField = React.forwardRef<HTMLDivElement, FormFieldProps>(
  ({ children, className, flex = true }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('flex flex-col gap-2', flex && 'flex-1', className)}
      >
        {children}
      </div>
    )
  }
)

FormField.displayName = 'FormField'

export { Form, FormGroup, FormRow, FormField }
