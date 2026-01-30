import React, { Component, ErrorInfo, ReactNode } from 'react'
import Button from './Button'
import Card from './Card'

interface PageErrorBoundaryProps {
  children: ReactNode
  pageName?: string
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface PageErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Error boundary component for catching and displaying page-level errors.
 *
 * Wraps page components to catch JavaScript errors anywhere in the child
 * component tree, log those errors, and display a fallback UI.
 *
 * @example
 * <PageErrorBoundary pageName="Dashboard">
 *   <Dashboard />
 * </PageErrorBoundary>
 */
class PageErrorBoundary extends Component<
  PageErrorBoundaryProps,
  PageErrorBoundaryState
> {
  constructor(props: PageErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<PageErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console
    console.error('Page error caught by boundary:', error, errorInfo)

    // Store error info for display
    this.setState({ errorInfo })

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Could also log to an error reporting service here
    // e.g., Sentry.captureException(error)
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleGoHome = (): void => {
    window.location.href = '/'
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <Card className="max-w-lg w-full">
            <div className="p-6 text-center">
              {/* Error Icon */}
              <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-red-600 dark:text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>

              {/* Error Message */}
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Something went wrong
              </h2>

              {this.props.pageName && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                  Error on {this.props.pageName} page
                </p>
              )}

              <p className="text-gray-600 dark:text-gray-300 mb-6">
                We're sorry, but something unexpected happened. You can try
                refreshing the page or going back to the home page.
              </p>

              {/* Error Details (collapsible) */}
              {this.state.error && (
                <details className="mb-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                    Technical Details
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono overflow-auto max-h-32">
                    <p className="text-red-600 dark:text-red-400">
                      {this.state.error.name}: {this.state.error.message}
                    </p>
                    {this.state.errorInfo?.componentStack && (
                      <pre className="mt-2 text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    )}
                  </div>
                </details>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button variant="primary" onClick={this.handleRetry}>
                  Try Again
                </Button>
                <Button variant="secondary" onClick={this.handleReload}>
                  Reload Page
                </Button>
                <Button variant="secondary" onClick={this.handleGoHome}>
                  Go to Home
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

export default PageErrorBoundary

/**
 * Hook to wrap a component with an error boundary.
 * Useful for functional components.
 *
 * @example
 * const SafeDashboard = withErrorBoundary(Dashboard, 'Dashboard')
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  pageName?: string
): React.FC<P> {
  const WithErrorBoundary: React.FC<P> = (props) => (
    <PageErrorBoundary pageName={pageName}>
      <WrappedComponent {...props} />
    </PageErrorBoundary>
  )

  WithErrorBoundary.displayName = `WithErrorBoundary(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`

  return WithErrorBoundary
}
