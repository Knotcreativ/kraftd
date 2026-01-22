'use client'

import { ReactNode, Component, ReactElement } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactElement
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="rounded-md bg-red-50 p-6 text-center">
            <h3 className="text-lg font-medium text-red-900">Something went wrong</h3>
            <p className="mt-2 text-sm text-red-700">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="mt-4 btn btn-primary"
            >
              Try again
            </button>
          </div>
        )
      )
    }

    return this.props.children
  }
}
