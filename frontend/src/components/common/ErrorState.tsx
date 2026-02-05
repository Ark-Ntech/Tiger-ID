import { useState } from 'react'
import { ExclamationTriangleIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'

interface ErrorStateProps {
  /** Title displayed at the top of the error state */
  title?: string
  /** The error message or Error object to display */
  error: string | Error
  /** Optional callback for retry action */
  onRetry?: () => void
  /** Optional callback for skip action (useful for workflow errors) */
  onSkip?: () => void
  /** Optional callback to proceed with partial results */
  onUsePartial?: () => void
  /** Show expanded error details including stack trace */
  showDetails?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * ErrorState component displays error information with recovery options.
 * Used for displaying errors in workflows, API failures, and other error scenarios.
 */
const ErrorState = ({
  title = 'Something went wrong',
  error,
  onRetry,
  onSkip,
  onUsePartial,
  showDetails = false,
  className,
}: ErrorStateProps) => {
  const [isDetailsExpanded, setIsDetailsExpanded] = useState(false)

  // Extract error message and stack trace
  const errorMessage = error instanceof Error ? error.message : error
  const errorStack = error instanceof Error ? error.stack : null

  const hasActions = onRetry || onSkip || onUsePartial
  const hasDetails = showDetails && errorStack

  return (
    <div
      data-testid="error-state"
      className={cn(
        'rounded-xl border-2 border-red-300 bg-red-50 p-6',
        'dark:bg-red-950/30 dark:border-red-800',
        'shadow-critical',
        className
      )}
    >
      {/* Header with icon and title */}
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/50">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <h3
            data-testid="error-state-title"
            className="text-lg font-semibold text-red-800 dark:text-red-200"
          >
            {title}
          </h3>

          {/* Error message in code block */}
          <div
            data-testid="error-state-message"
            className={cn(
              'mt-3 p-3 rounded-lg',
              'bg-red-100/50 dark:bg-red-900/30',
              'border border-red-200 dark:border-red-800',
              'max-h-32 overflow-auto'
            )}
          >
            <pre className="text-sm font-mono text-red-700 dark:text-red-300 whitespace-pre-wrap break-words">
              {errorMessage}
            </pre>
          </div>

          {/* Collapsible details section */}
          {hasDetails && (
            <div className="mt-3">
              <button
                data-testid="error-state-details-toggle"
                onClick={() => setIsDetailsExpanded(!isDetailsExpanded)}
                className={cn(
                  'flex items-center gap-1.5 text-sm font-medium',
                  'text-red-600 dark:text-red-400',
                  'hover:text-red-700 dark:hover:text-red-300',
                  'transition-colors'
                )}
              >
                {isDetailsExpanded ? (
                  <ChevronUpIcon className="h-4 w-4" />
                ) : (
                  <ChevronDownIcon className="h-4 w-4" />
                )}
                {isDetailsExpanded ? 'Hide details' : 'Show details'}
              </button>

              {isDetailsExpanded && (
                <div
                  className={cn(
                    'mt-2 p-3 rounded-lg',
                    'bg-tactical-900 dark:bg-tactical-950',
                    'border border-red-300 dark:border-red-800',
                    'max-h-48 overflow-auto'
                  )}
                >
                  <pre className="text-xs font-mono text-tactical-300 whitespace-pre-wrap break-words">
                    {errorStack}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          {hasActions && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {onRetry && (
                <button
                  data-testid="error-state-retry"
                  onClick={onRetry}
                  className={cn(
                    'inline-flex items-center justify-center',
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'bg-tiger-orange text-white',
                    'hover:bg-tiger-orange-dark',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2',
                    'transition-colors'
                  )}
                >
                  Retry
                </button>
              )}

              {onUsePartial && (
                <button
                  data-testid="error-state-use-partial"
                  onClick={onUsePartial}
                  className={cn(
                    'inline-flex items-center justify-center',
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'bg-tactical-200 text-tactical-900',
                    'hover:bg-tactical-300',
                    'dark:bg-tactical-700 dark:text-tactical-100 dark:hover:bg-tactical-600',
                    'focus:outline-none focus:ring-2 focus:ring-tactical-500 focus:ring-offset-2',
                    'transition-colors'
                  )}
                >
                  Use Partial Results
                </button>
              )}

              {onSkip && (
                <button
                  data-testid="error-state-skip"
                  onClick={onSkip}
                  className={cn(
                    'inline-flex items-center justify-center',
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'text-tactical-700 dark:text-tactical-300',
                    'hover:bg-tactical-100 dark:hover:bg-tactical-800',
                    'focus:outline-none focus:ring-2 focus:ring-tactical-500 focus:ring-offset-2',
                    'transition-colors'
                  )}
                >
                  Skip
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export { ErrorState }
export default ErrorState
