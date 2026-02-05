/**
 * FacilityCrawlGrid Component
 *
 * Displays a grid of facility cards showing their current crawl status
 * in real-time. Each card shows progress, image count, and status indicators
 * with appropriate styling based on the crawl state.
 *
 * Design: Tactical/professional aesthetic matching the Tiger ID system.
 * Uses tiger-orange for active crawls, emerald for completed, amber for
 * rate-limited, and red for errors.
 */

import { cn } from '../../utils/cn'
import { Skeleton } from '../common/Skeleton'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline'
import { ArrowPathIcon } from '@heroicons/react/24/solid'

// ============================================================================
// Types
// ============================================================================

export type CrawlStatus = 'crawling' | 'completed' | 'waiting' | 'error' | 'rate_limited'

export interface FacilityCrawlStatus {
  facility_id: string
  facility_name: string
  status: CrawlStatus
  progress: number // 0-100
  images_found: number
  last_update: string
  error_message?: string
  wait_seconds?: number // for rate limited status
}

export interface FacilityCrawlGridProps {
  facilities: FacilityCrawlStatus[]
  onFacilityClick?: (facilityId: string) => void
  isLoading?: boolean
  skeletonCount?: number
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_CONFIG: Record<CrawlStatus, {
  label: string
  icon: React.ComponentType<{ className?: string }>
  bgClass: string
  textClass: string
  borderClass: string
  progressClass: string
  iconClass: string
}> = {
  crawling: {
    label: 'Crawling',
    icon: ArrowPathIcon,
    bgClass: 'bg-white dark:bg-tactical-800',
    textClass: 'text-tactical-900 dark:text-tactical-100',
    borderClass: 'border-tiger-orange/50 dark:border-tiger-orange/40',
    progressClass: 'bg-tiger-orange',
    iconClass: 'text-tiger-orange animate-spin',
  },
  completed: {
    label: 'Done',
    icon: CheckCircleIcon,
    bgClass: 'bg-white dark:bg-tactical-800',
    textClass: 'text-tactical-900 dark:text-tactical-100',
    borderClass: 'border-emerald-300 dark:border-emerald-700',
    progressClass: 'bg-emerald-500',
    iconClass: 'text-emerald-500',
  },
  waiting: {
    label: 'Waiting',
    icon: ClockIcon,
    bgClass: 'bg-tactical-50 dark:bg-tactical-800/80',
    textClass: 'text-tactical-600 dark:text-tactical-400',
    borderClass: 'border-tactical-300 dark:border-tactical-600',
    progressClass: 'bg-tactical-400',
    iconClass: 'text-tactical-400',
  },
  error: {
    label: 'Error',
    icon: ExclamationCircleIcon,
    bgClass: 'bg-red-50 dark:bg-red-900/20',
    textClass: 'text-tactical-900 dark:text-tactical-100',
    borderClass: 'border-red-300 dark:border-red-700',
    progressClass: 'bg-red-500',
    iconClass: 'text-red-500',
  },
  rate_limited: {
    label: 'Rate Limited',
    icon: ExclamationTriangleIcon,
    bgClass: 'bg-amber-50 dark:bg-amber-900/20',
    textClass: 'text-tactical-900 dark:text-tactical-100',
    borderClass: 'border-amber-300 dark:border-amber-700',
    progressClass: 'bg-amber-500',
    iconClass: 'text-amber-500',
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
  const isAnimated = status === 'crawling'

  return (
    <div
      data-testid="facility-progress-bar"
      className="h-2 rounded-full bg-tactical-200 dark:bg-tactical-700 overflow-hidden"
    >
      <div
        className={cn(
          'h-full rounded-full transition-all duration-500 ease-out',
          config.progressClass,
          isAnimated && 'relative overflow-hidden'
        )}
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      >
        {isAnimated && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-progress" />
        )}
      </div>
    </div>
  )
}

interface StatusIndicatorProps {
  status: CrawlStatus
  waitSeconds?: number
}

const StatusIndicator = ({ status, waitSeconds }: StatusIndicatorProps) => {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  return (
    <div
      data-testid="facility-status"
      className="flex items-center gap-1.5"
    >
      <Icon className={cn('w-4 h-4', config.iconClass)} />
      <span className={cn(
        'text-xs font-medium',
        status === 'completed' && 'text-emerald-600 dark:text-emerald-400',
        status === 'crawling' && 'text-tiger-orange',
        status === 'waiting' && 'text-tactical-500 dark:text-tactical-400',
        status === 'error' && 'text-red-600 dark:text-red-400',
        status === 'rate_limited' && 'text-amber-600 dark:text-amber-400',
      )}>
        {status === 'rate_limited' && waitSeconds
          ? `Wait ${waitSeconds}s`
          : config.label}
        {status === 'completed' && ' \u2713'}
      </span>
    </div>
  )
}

interface FacilityCardProps {
  facility: FacilityCrawlStatus
  onClick?: () => void
}

const FacilityCard = ({ facility, onClick }: FacilityCardProps) => {
  const config = STATUS_CONFIG[facility.status]
  const isClickable = !!onClick

  return (
    <div
      data-testid={`facility-crawl-card-${facility.facility_id}`}
      onClick={onClick}
      className={cn(
        'relative rounded-lg border p-4 transition-all duration-200',
        config.bgClass,
        config.borderClass,
        isClickable && 'cursor-pointer hover:shadow-tactical-lg hover:-translate-y-0.5',
        isClickable && 'active:translate-y-0 active:shadow-tactical',
        facility.status === 'crawling' && 'ring-1 ring-tiger-orange/30'
      )}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.()
        }
      } : undefined}
    >
      {/* Facility Name */}
      <h3 className={cn(
        'font-semibold text-sm truncate mb-2',
        config.textClass
      )}>
        {facility.facility_name}
      </h3>

      {/* Progress Bar */}
      <div className="mb-2">
        <ProgressBar progress={facility.progress} status={facility.status} />
      </div>

      {/* Progress Percentage (for crawling status) */}
      {facility.status === 'crawling' && (
        <p className="text-xs font-mono text-tiger-orange mb-2">
          {facility.progress}%
        </p>
      )}

      {/* Status and Image Count Row */}
      <div className="flex items-center justify-between">
        <StatusIndicator
          status={facility.status}
          waitSeconds={facility.wait_seconds}
        />

        {/* Image Count */}
        <div className="flex items-center gap-1 text-xs text-tactical-500 dark:text-tactical-400">
          <PhotoIcon className="w-3.5 h-3.5" />
          <span>{facility.images_found} imgs</span>
        </div>
      </div>

      {/* Error Message Tooltip */}
      {facility.status === 'error' && facility.error_message && (
        <p className="mt-2 text-xs text-red-600 dark:text-red-400 truncate" title={facility.error_message}>
          {facility.error_message}
        </p>
      )}

      {/* Active crawl glow effect */}
      {facility.status === 'crawling' && (
        <div className="absolute inset-0 rounded-lg ring-2 ring-tiger-orange/20 animate-pulse-slow pointer-events-none" />
      )}
    </div>
  )
}

// ============================================================================
// Skeleton Components
// ============================================================================

/**
 * Single facility card skeleton
 */
const FacilityCardSkeleton = () => {
  return (
    <div
      data-testid="facility-crawl-card-skeleton"
      className={cn(
        'relative rounded-lg border p-4',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700'
      )}
    >
      {/* Facility name */}
      <Skeleton variant="text" className="h-4 w-3/4 mb-2" />

      {/* Progress bar */}
      <Skeleton variant="rounded" className="h-2 w-full mb-2" />

      {/* Status and image count row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Skeleton variant="circular" className="w-4 h-4" />
          <Skeleton variant="text" className="h-3 w-14" />
        </div>
        <div className="flex items-center gap-1">
          <Skeleton variant="rounded" className="w-3.5 h-3.5" />
          <Skeleton variant="text" className="h-3 w-10" />
        </div>
      </div>
    </div>
  )
}

/**
 * Grid skeleton for loading state
 */
const FacilityCrawlGridSkeleton = ({
  count = 6,
  className,
}: {
  count?: number
  className?: string
}) => {
  return (
    <div
      data-testid="facility-crawl-grid-skeleton"
      className={cn(
        'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4',
        className
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <FacilityCardSkeleton key={i} />
      ))}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export const FacilityCrawlGrid = ({
  facilities,
  onFacilityClick,
  isLoading = false,
  skeletonCount = 6,
  className,
}: FacilityCrawlGridProps) => {
  // Show skeleton when loading
  if (isLoading) {
    return <FacilityCrawlGridSkeleton count={skeletonCount} className={className} />
  }

  if (facilities.length === 0) {
    return (
      <div
        data-testid="facility-crawl-grid"
        className={cn(
          'flex flex-col items-center justify-center py-12 text-center',
          'bg-tactical-50 dark:bg-tactical-800/50 rounded-xl border border-dashed border-tactical-300 dark:border-tactical-600',
          className
        )}
      >
        <ClockIcon className="w-12 h-12 text-tactical-300 dark:text-tactical-600 mb-4" />
        <p className="text-tactical-600 dark:text-tactical-400 font-medium">
          No facilities currently being crawled
        </p>
        <p className="text-sm text-tactical-500 dark:text-tactical-500 mt-1">
          Facility crawl status will appear here when crawling begins
        </p>
      </div>
    )
  }

  return (
    <div
      data-testid="facility-crawl-grid"
      className={cn(
        'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4',
        className
      )}
    >
      {facilities.map((facility) => (
        <FacilityCard
          key={facility.facility_id}
          facility={facility}
          onClick={onFacilityClick ? () => onFacilityClick(facility.facility_id) : undefined}
        />
      ))}
    </div>
  )
}

export default FacilityCrawlGrid
