/**
 * CrawlProgressCard Component
 *
 * A compact card showing individual facility crawl status with progress bar,
 * image counts, and status-based styling. Designed for the discovery pipeline
 * dashboard to display real-time crawl progress for each facility.
 *
 * Design: Tactical/professional aesthetic matching the Tiger ID system.
 * Uses status-based border colors with appropriate icons and animations.
 */

import { useEffect, useState, useCallback } from 'react'
import { cn } from '../../utils/cn'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PhotoIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

// ============================================================================
// Types
// ============================================================================

export type CrawlStatus = 'idle' | 'crawling' | 'completed' | 'rate_limited' | 'error'

export interface CrawlProgressCardProps {
  facilityId: string
  facilityName: string
  status: CrawlStatus
  progress: number // 0-100
  imagesFound: number
  tigersDetected?: number
  lastActivity?: string
  rateLimitWait?: number // seconds
  errorMessage?: string
  onRetry?: () => void
  onClick?: () => void
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_CONFIG: Record<CrawlStatus, {
  label: string
  icon: React.ComponentType<{ className?: string }>
  borderClass: string
  progressClass: string
  iconClass: string
  bgClass: string
  textClass: string
}> = {
  idle: {
    label: 'Idle',
    icon: ClockIcon,
    borderClass: 'border-tactical-600 dark:border-tactical-500',
    progressClass: 'bg-tactical-400',
    iconClass: 'text-tactical-500 dark:text-tactical-400',
    bgClass: 'bg-white dark:bg-tactical-800',
    textClass: 'text-tactical-600 dark:text-tactical-400',
  },
  crawling: {
    label: 'Crawling',
    icon: ArrowPathIcon,
    borderClass: 'border-tiger-orange dark:border-tiger-orange-light',
    progressClass: 'bg-tiger-orange',
    iconClass: 'text-tiger-orange animate-spin',
    bgClass: 'bg-white dark:bg-tactical-800',
    textClass: 'text-tiger-orange',
  },
  completed: {
    label: 'Completed',
    icon: CheckCircleIcon,
    borderClass: 'border-status-success dark:border-emerald-500',
    progressClass: 'bg-status-success',
    iconClass: 'text-status-success',
    bgClass: 'bg-white dark:bg-tactical-800',
    textClass: 'text-status-success',
  },
  rate_limited: {
    label: 'Rate Limited',
    icon: ExclamationTriangleIcon,
    borderClass: 'border-status-warning dark:border-amber-500',
    progressClass: 'bg-status-warning',
    iconClass: 'text-status-warning',
    bgClass: 'bg-amber-50 dark:bg-amber-900/20',
    textClass: 'text-status-warning',
  },
  error: {
    label: 'Error',
    icon: ExclamationCircleIcon,
    borderClass: 'border-status-danger dark:border-red-500',
    progressClass: 'bg-status-danger',
    iconClass: 'text-status-danger',
    bgClass: 'bg-red-50 dark:bg-red-900/20',
    textClass: 'text-status-danger',
  },
}

// ============================================================================
// Sub-Components
// ============================================================================

interface ProgressBarProps {
  progress: number
  status: CrawlStatus
}

const ProgressBar = ({ progress, status }: ProgressBarProps) => {
  const config = STATUS_CONFIG[status]
  const clampedProgress = Math.min(100, Math.max(0, progress))
  const isAnimated = status === 'crawling'

  return (
    <div
      data-testid="crawl-progress-bar"
      className="h-2 rounded-full bg-tactical-200 dark:bg-tactical-700 overflow-hidden"
    >
      <div
        className={cn(
          'h-full rounded-full transition-all duration-500 ease-out',
          config.progressClass,
          isAnimated && 'relative overflow-hidden'
        )}
        style={{ width: `${clampedProgress}%` }}
      >
        {isAnimated && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-progress" />
        )}
      </div>
    </div>
  )
}

interface RateLimitCountdownProps {
  seconds: number
}

const RateLimitCountdown = ({ seconds: initialSeconds }: RateLimitCountdownProps) => {
  const [seconds, setSeconds] = useState(initialSeconds)

  useEffect(() => {
    setSeconds(initialSeconds)
  }, [initialSeconds])

  useEffect(() => {
    if (seconds <= 0) return

    const interval = setInterval(() => {
      setSeconds((prev) => Math.max(0, prev - 1))
    }, 1000)

    return () => clearInterval(interval)
  }, [seconds])

  const formatTime = (s: number): string => {
    if (s >= 60) {
      const mins = Math.floor(s / 60)
      const secs = s % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
    return `${s}s`
  }

  return (
    <span
      data-testid="rate-limit-countdown"
      className="font-mono text-xs text-amber-600 dark:text-amber-400"
    >
      {formatTime(seconds)}
    </span>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export const CrawlProgressCard = ({
  facilityId,
  facilityName,
  status,
  progress,
  imagesFound,
  tigersDetected,
  lastActivity,
  rateLimitWait,
  errorMessage,
  onRetry,
  onClick,
  className,
}: CrawlProgressCardProps) => {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  const isClickable = !!onClick
  const showRetry = status === 'error' && !!onRetry

  const handleRetry = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      onRetry?.()
    },
    [onRetry]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault()
        onClick?.()
      }
    },
    [isClickable, onClick]
  )

  return (
    <div
      data-testid={`crawl-progress-card-${facilityId}`}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      className={cn(
        'relative rounded-lg border-2 p-4 transition-all duration-200',
        config.bgClass,
        config.borderClass,
        isClickable && 'cursor-pointer',
        isClickable && 'hover:shadow-tactical-lg hover:-translate-y-0.5',
        isClickable && 'active:translate-y-0 active:shadow-tactical',
        status === 'crawling' && 'animate-pulse-glow',
        className
      )}
    >
      {/* Header: Facility Name and Status Icon */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <h3
          data-testid="crawl-card-facility-name"
          className="font-semibold text-sm text-tactical-900 dark:text-tactical-100 truncate flex-1"
          title={facilityName}
        >
          {facilityName}
        </h3>
        <Icon
          data-testid="crawl-status-icon"
          className={cn('w-5 h-5 flex-shrink-0', config.iconClass)}
        />
      </div>

      {/* Progress Bar */}
      <div className="mb-2">
        <ProgressBar progress={progress} status={status} />
      </div>

      {/* Progress Percentage */}
      <div className="flex items-center justify-between mb-2">
        <span
          data-testid="crawl-progress-percentage"
          className={cn(
            'text-xs font-mono',
            status === 'crawling' ? 'text-tiger-orange' : 'text-tactical-500 dark:text-tactical-400'
          )}
        >
          {progress}%
        </span>
        {status === 'rate_limited' && rateLimitWait && rateLimitWait > 0 && (
          <RateLimitCountdown seconds={rateLimitWait} />
        )}
      </div>

      {/* Stats Row: Images and Tigers */}
      <div className="flex items-center justify-between gap-2 text-xs">
        <div
          data-testid="crawl-images-found"
          className="flex items-center gap-1.5 text-tactical-600 dark:text-tactical-400"
        >
          <PhotoIcon className="w-4 h-4" />
          <span>{imagesFound} imgs</span>
        </div>

        {tigersDetected !== undefined && (
          <div
            data-testid="crawl-tigers-detected"
            className="flex items-center gap-1.5 text-tiger-orange font-medium"
          >
            <span>{tigersDetected} tigers</span>
          </div>
        )}
      </div>

      {/* Status Label */}
      <div
        data-testid="crawl-status-label"
        className={cn('flex items-center gap-1.5 mt-2 text-xs font-medium', config.textClass)}
      >
        {status === 'completed' && <CheckCircleIcon className="w-3.5 h-3.5" />}
        <span>
          {status === 'rate_limited' && rateLimitWait
            ? `Rate limited - waiting`
            : config.label}
        </span>
      </div>

      {/* Last Activity (for non-error states) */}
      {lastActivity && status !== 'error' && (
        <p
          data-testid="crawl-last-activity"
          className="text-2xs text-tactical-500 dark:text-tactical-500 mt-1 truncate"
        >
          {lastActivity}
        </p>
      )}

      {/* Error Message */}
      {status === 'error' && errorMessage && (
        <p
          data-testid="crawl-error-message"
          className="text-xs text-red-600 dark:text-red-400 mt-2 truncate"
          title={errorMessage}
        >
          {errorMessage}
        </p>
      )}

      {/* Retry Button for Error State */}
      {showRetry && (
        <button
          data-testid="crawl-retry-button"
          type="button"
          onClick={handleRetry}
          className={cn(
            'mt-3 w-full px-3 py-1.5 text-xs font-medium rounded-md',
            'bg-red-100 text-red-700 hover:bg-red-200',
            'dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:ring-offset-1',
            'dark:focus:ring-offset-tactical-800'
          )}
        >
          <span className="flex items-center justify-center gap-1.5">
            <ArrowPathIcon className="w-3.5 h-3.5" />
            Retry
          </span>
        </button>
      )}

      {/* Active Crawl Glow Effect */}
      {status === 'crawling' && (
        <div
          data-testid="crawl-active-indicator"
          className="absolute inset-0 rounded-lg ring-2 ring-tiger-orange/30 animate-pulse-slow pointer-events-none"
        />
      )}
    </div>
  )
}

export default CrawlProgressCard
