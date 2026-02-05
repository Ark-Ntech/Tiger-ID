import { useCallback } from 'react'
import { cn } from '../../../utils/cn'
import Badge from '../../common/Badge'
import { AnimatedNumber } from '../../common/AnimatedNumber'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'

/**
 * Status type for individual model progress
 */
export type ModelStatus = 'pending' | 'running' | 'completed' | 'error'

/**
 * Progress data for a single ML model
 */
export interface ModelProgress {
  /** Model identifier (e.g., 'wildlife_tools', 'cvwc2019_reid') */
  model: string
  /** Progress percentage (0-100) */
  progress: number
  /** Current status of the model */
  status: ModelStatus
  /** Number of embeddings generated (optional) */
  embeddings?: number
  /** Processing time in milliseconds (optional) */
  processingTime?: number
  /** Error message if status is 'error' (optional) */
  errorMessage?: string
}

/**
 * Props for the ModelProgressGrid component
 */
export interface ModelProgressGridProps {
  /** Array of model progress data */
  models: ModelProgress[]
  /** Optional title for the grid section */
  title?: string
  /** Additional CSS classes */
  className?: string
  /** Callback when retry is clicked for an errored model */
  onRetry?: (model: string) => void
}

/**
 * Display name mapping for model identifiers
 */
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  wildlife_tools: 'Wildlife Tools',
  cvwc2019_reid: 'CVWC 2019',
  transreid: 'TransReID',
  megadescriptor_b: 'MegaDescriptor',
  tiger_reid: 'Tiger ReID',
  rapid_reid: 'Rapid ReID',
}

/**
 * Model weight info for display
 */
const MODEL_WEIGHTS: Record<string, number> = {
  wildlife_tools: 0.40,
  cvwc2019_reid: 0.30,
  transreid: 0.20,
  megadescriptor_b: 0.15,
  tiger_reid: 0.10,
  rapid_reid: 0.05,
}

/**
 * Get display name for a model identifier
 */
function getModelDisplayName(model: string): string {
  return MODEL_DISPLAY_NAMES[model] || model
}

/**
 * Get the status icon for a model
 */
function getStatusIcon(status: ModelStatus): React.ReactNode {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon className="w-5 h-5 text-emerald-500" />
    case 'running':
      return <ArrowPathIcon className="w-5 h-5 text-tiger-orange animate-spin" />
    case 'error':
      return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
    case 'pending':
    default:
      return <ClockIcon className="w-5 h-5 text-tactical-400" />
  }
}

/**
 * Get the progress bar color classes based on status
 */
function getProgressBarClasses(status: ModelStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-emerald-500'
    case 'running':
      return 'bg-tiger-orange'
    case 'error':
      return 'bg-red-500'
    case 'pending':
    default:
      return 'bg-tactical-300 dark:bg-tactical-600'
  }
}

/**
 * Get the card border/background classes based on status
 */
function getCardClasses(status: ModelStatus): string {
  switch (status) {
    case 'completed':
      return cn(
        'border-emerald-200 bg-emerald-50/50',
        'dark:border-emerald-800/50 dark:bg-emerald-900/10'
      )
    case 'running':
      return cn(
        'border-tiger-orange/50 bg-tiger-orange/5',
        'dark:border-tiger-orange/30 dark:bg-tiger-orange/5',
        'shadow-tiger ring-1 ring-tiger-orange/20'
      )
    case 'error':
      return cn(
        'border-red-200 bg-red-50/50',
        'dark:border-red-800/50 dark:bg-red-900/10'
      )
    case 'pending':
    default:
      return cn(
        'border-tactical-200 bg-tactical-50/50',
        'dark:border-tactical-700 dark:bg-tactical-800/50'
      )
  }
}

/**
 * Format processing time in a human-readable format
 */
function formatProcessingTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Single model card component
 */
interface ModelCardProps {
  model: ModelProgress
  onRetry?: (model: string) => void
}

function ModelCard({ model, onRetry }: ModelCardProps): React.ReactElement {
  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry(model.model)
    }
  }, [onRetry, model.model])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.key === 'Enter' || e.key === ' ') && model.status === 'error' && onRetry) {
        e.preventDefault()
        handleRetry()
      }
    },
    [handleRetry, model.status, onRetry]
  )

  const weight = MODEL_WEIGHTS[model.model]

  return (
    <div
      data-testid={`model-card-${model.model}`}
      className={cn(
        'relative flex flex-col rounded-lg border p-3',
        'transition-all duration-300',
        getCardClasses(model.status)
      )}
    >
      {/* Header: Model name and status icon */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            data-testid={`model-status-icon-${model.model}`}
            className="flex-shrink-0"
          >
            {getStatusIcon(model.status)}
          </span>
          <span
            className={cn(
              'font-medium text-sm truncate',
              'text-tactical-900 dark:text-tactical-100'
            )}
            title={getModelDisplayName(model.model)}
          >
            {getModelDisplayName(model.model)}
          </span>
        </div>
        {weight && (
          <span
            data-testid={`model-weight-${model.model}`}
            className={cn(
              'text-2xs font-mono px-1.5 py-0.5 rounded',
              'bg-tactical-100 text-tactical-600',
              'dark:bg-tactical-700 dark:text-tactical-400'
            )}
          >
            {(weight * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-2">
        <div
          data-testid={`model-progress-bar-${model.model}`}
          className={cn(
            'h-2 w-full rounded-full overflow-hidden',
            'bg-tactical-200 dark:bg-tactical-700'
          )}
        >
          <div
            className={cn(
              'h-full rounded-full',
              'transition-all duration-500 ease-out',
              getProgressBarClasses(model.status)
            )}
            style={{ width: `${Math.min(100, Math.max(0, model.progress))}%` }}
            role="progressbar"
            aria-valuenow={model.progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${getModelDisplayName(model.model)} progress`}
          />
        </div>
      </div>

      {/* Progress percentage and metadata */}
      <div className="flex items-center justify-between text-xs">
        <span
          data-testid={`model-progress-text-${model.model}`}
          className={cn(
            'font-medium',
            model.status === 'completed'
              ? 'text-emerald-600 dark:text-emerald-400'
              : model.status === 'running'
              ? 'text-tiger-orange dark:text-tiger-orange-light'
              : model.status === 'error'
              ? 'text-red-600 dark:text-red-400'
              : 'text-tactical-500 dark:text-tactical-400'
          )}
        >
          <AnimatedNumber
            value={model.progress}
            duration={800}
            suffix="%"
            easing="easeOut"
          />
        </span>

        {/* Metadata: embeddings or processing time */}
        <div className="flex items-center gap-2">
          {model.embeddings !== undefined && model.status === 'completed' && (
            <span
              data-testid={`model-embeddings-${model.model}`}
              className="text-tactical-500 dark:text-tactical-400"
            >
              {model.embeddings} emb
            </span>
          )}
          {model.processingTime !== undefined && model.status === 'completed' && (
            <span
              data-testid={`model-time-${model.model}`}
              className="text-tactical-500 dark:text-tactical-400"
            >
              {formatProcessingTime(model.processingTime)}
            </span>
          )}
        </div>
      </div>

      {/* Error state with retry button */}
      {model.status === 'error' && (
        <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-800/50">
          <p
            data-testid={`model-error-${model.model}`}
            className="text-xs text-red-600 dark:text-red-400 mb-2 line-clamp-2"
            title={model.errorMessage}
          >
            {model.errorMessage || 'An error occurred'}
          </p>
          {onRetry && (
            <button
              type="button"
              data-testid={`model-retry-${model.model}`}
              onClick={handleRetry}
              onKeyDown={handleKeyDown}
              className={cn(
                'w-full px-2 py-1 rounded text-xs font-medium',
                'bg-red-100 text-red-700 border border-red-200',
                'hover:bg-red-200 hover:border-red-300',
                'dark:bg-red-900/30 dark:text-red-300 dark:border-red-800',
                'dark:hover:bg-red-900/50 dark:hover:border-red-700',
                'transition-colors duration-150',
                'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1',
                'dark:focus:ring-offset-tactical-800'
              )}
            >
              Retry
            </button>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * ModelProgressGrid displays a responsive grid of model progress cards
 * for visualizing parallel 6-model stripe analysis.
 *
 * Features:
 * - Responsive grid: 2x3 on mobile, 3x2 on tablet, 6x1 on desktop
 * - Progress bars with smooth animations
 * - Status indicators with icons
 * - Completion count badge
 * - Error state with retry option
 * - Model weights display
 * - Processing time and embeddings metadata
 */
export function ModelProgressGrid({
  models,
  title = 'Stripe Analysis',
  className,
  onRetry,
}: ModelProgressGridProps): React.ReactElement {
  const completedCount = models.filter((m) => m.status === 'completed').length
  const totalCount = models.length
  const hasErrors = models.some((m) => m.status === 'error')
  const isRunning = models.some((m) => m.status === 'running')

  return (
    <div
      data-testid="model-progress-grid"
      className={cn(
        'rounded-xl border p-4',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700',
        'shadow-tactical',
        className
      )}
    >
      {/* Header with title and completion badge */}
      <div className="flex items-center justify-between mb-4">
        <h3
          data-testid="model-progress-title"
          className={cn(
            'font-semibold text-tactical-900 dark:text-tactical-100',
            'text-base'
          )}
        >
          {title}
        </h3>
        <Badge
          data-testid="model-progress-badge"
          variant={
            completedCount === totalCount
              ? 'success'
              : hasErrors
              ? 'danger'
              : isRunning
              ? 'tiger'
              : 'default'
          }
          size="sm"
          dot={isRunning}
        >
          {completedCount}/{totalCount}{' '}
          {completedCount === totalCount ? (
            <CheckCircleIcon className="inline w-3.5 h-3.5 ml-0.5" />
          ) : hasErrors ? (
            <ExclamationTriangleIcon className="inline w-3.5 h-3.5 ml-0.5" />
          ) : null}
        </Badge>
      </div>

      {/* Responsive grid of model cards */}
      <div
        data-testid="model-progress-cards"
        className={cn(
          'grid gap-3',
          // 2 columns on mobile (2x3 for 6 models)
          'grid-cols-2',
          // 3 columns on tablet (3x2 for 6 models)
          'sm:grid-cols-3',
          // 6 columns on desktop (6x1 for 6 models)
          'lg:grid-cols-6'
        )}
      >
        {models.map((model) => (
          <ModelCard key={model.model} model={model} onRetry={onRetry} />
        ))}
      </div>

      {/* Overall progress indicator */}
      {totalCount > 0 && (
        <div className="mt-4 pt-3 border-t border-tactical-200 dark:border-tactical-700">
          <div className="flex items-center justify-between mb-1.5">
            <span
              data-testid="model-overall-label"
              className="text-xs font-medium text-tactical-600 dark:text-tactical-400"
            >
              Overall Progress
            </span>
            <span
              data-testid="model-overall-percent"
              className={cn(
                'text-xs font-medium',
                completedCount === totalCount
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-tactical-600 dark:text-tactical-400'
              )}
            >
              <AnimatedNumber
                value={Math.round((completedCount / totalCount) * 100)}
                duration={600}
                suffix="%"
                easing="easeOut"
              />
            </span>
          </div>
          <div
            data-testid="model-overall-progress-bar"
            className={cn(
              'h-1.5 w-full rounded-full overflow-hidden',
              'bg-tactical-200 dark:bg-tactical-700'
            )}
          >
            <div
              className={cn(
                'h-full rounded-full',
                'transition-all duration-500 ease-out',
                completedCount === totalCount
                  ? 'bg-emerald-500'
                  : hasErrors
                  ? 'bg-amber-500'
                  : 'bg-tiger-orange'
              )}
              style={{ width: `${(completedCount / totalCount) * 100}%` }}
              role="progressbar"
              aria-valuenow={(completedCount / totalCount) * 100}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Overall model progress"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default ModelProgressGrid
