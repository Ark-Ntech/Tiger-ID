import { cn } from '../../utils/cn'

/**
 * Skeleton variant types
 * Supports both long-form and short-form names for developer convenience
 */
type SkeletonVariant =
  | 'text'
  | 'circular' | 'circle'  // aliases
  | 'rectangular' | 'rect' // aliases
  | 'rounded'
  | 'card'

interface SkeletonProps {
  className?: string
  variant?: SkeletonVariant
  width?: string | number
  height?: string | number
  animation?: 'pulse' | 'wave' | 'shimmer' | 'none'
  'data-testid'?: string
}

/**
 * Base skeleton loader component with shimmer animation support
 *
 * Variants:
 * - text: Rounded corners for text placeholders
 * - circular: Fully rounded for avatars/icons
 * - rectangular: No border radius
 * - rounded: Rounded corners (lg) for cards/buttons
 * - card: Full card shape with shadow
 *
 * Animations:
 * - pulse: Default pulsing opacity animation
 * - wave/shimmer: Gradient sweep animation (more visible loading indicator)
 * - none: Static skeleton
 */
export const Skeleton = ({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'shimmer',
  'data-testid': testId = 'skeleton',
}: SkeletonProps) => {
  // Normalize variant aliases
  const normalizedVariant = variant === 'circle' ? 'circular'
    : variant === 'rect' ? 'rectangular'
    : variant

  const variantClasses: Record<string, string> = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-lg',
    card: 'rounded-xl shadow-tactical',
  }

  const getAnimationClasses = () => {
    switch (animation) {
      case 'pulse':
        return 'animate-pulse'
      case 'wave':
      case 'shimmer':
        return 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent dark:before:via-white/10'
      case 'none':
      default:
        return ''
    }
  }

  return (
    <div
      data-testid={testId}
      className={cn(
        'bg-tactical-200 dark:bg-tactical-700',
        variantClasses[normalizedVariant],
        getAnimationClasses(),
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  )
}

/**
 * Card skeleton with common card layout
 */
export const CardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="card-skeleton"
      className={cn('card space-y-4', className)}
    >
      <Skeleton variant="text" className="h-6 w-3/4" />
      <div className="space-y-2">
        <Skeleton variant="text" className="h-4 w-full" />
        <Skeleton variant="text" className="h-4 w-5/6" />
        <Skeleton variant="text" className="h-4 w-4/6" />
      </div>
      <div className="flex gap-2 pt-2">
        <Skeleton variant="rounded" className="h-8 w-20" />
        <Skeleton variant="rounded" className="h-8 w-20" />
      </div>
    </div>
  )
}

/**
 * Tiger card skeleton matching TigerCard layout
 */
export const TigerCardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="tiger-card-skeleton"
      className={cn(
        'relative flex flex-col rounded-xl overflow-hidden',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200/50 dark:border-tactical-700/50',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-tactical-100 dark:border-tactical-700/50">
        <Skeleton variant="rounded" className="w-4 h-4 flex-shrink-0" />
        <Skeleton variant="text" className="h-4 flex-1" />
      </div>

      {/* Image placeholder */}
      <div className="relative aspect-square bg-tactical-100 dark:bg-tactical-900">
        <Skeleton variant="rectangular" className="w-full h-full" animation="shimmer" />
      </div>

      {/* Footer */}
      <div className="flex flex-col gap-2 px-3 py-3">
        {/* Facility */}
        <Skeleton variant="text" className="h-3 w-2/3" />

        {/* Confidence */}
        <div className="flex items-center justify-between gap-2">
          <Skeleton variant="text" className="h-4 w-12" />
          <div className="flex gap-0.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} variant="circular" className="w-2 h-2" />
            ))}
          </div>
        </div>

        {/* Status badge */}
        <Skeleton variant="rounded" className="h-5 w-16" />
      </div>
    </div>
  )
}

/**
 * Match card skeleton for investigation results
 */
export const MatchCardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="match-card-skeleton"
      className={cn(
        'border border-tactical-200 dark:border-tactical-700 rounded-xl p-4 bg-white dark:bg-tactical-800',
        className
      )}
    >
      <div className="flex items-center gap-4">
        {/* Rank badge */}
        <Skeleton variant="circular" className="w-8 h-8 flex-shrink-0" />

        {/* Image placeholder */}
        <Skeleton variant="rounded" className="w-20 h-20 flex-shrink-0" />

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton variant="text" className="h-5 w-1/3" />
            <Skeleton variant="rounded" className="h-6 w-16" />
            <Skeleton variant="rounded" className="h-6 w-20" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton variant="rounded" className="w-4 h-4" />
            <Skeleton variant="text" className="h-4 w-32" />
          </div>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} variant="circular" className="w-3 h-3" />
            ))}
            <Skeleton variant="text" className="h-3 w-16 ml-1" />
          </div>
        </div>

        {/* Expand button */}
        <Skeleton variant="rounded" className="w-8 h-8 flex-shrink-0" />
      </div>
    </div>
  )
}

/**
 * Facility crawl card skeleton
 */
export const FacilityCrawlCardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="facility-crawl-card-skeleton"
      className={cn(
        'relative rounded-lg border p-4',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700',
        className
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
 * Map skeleton for map loading states
 */
export const MapSkeleton = ({
  className,
  height = '400px'
}: {
  className?: string
  height?: string
}) => {
  return (
    <div
      data-testid="map-skeleton"
      className={cn(
        'relative rounded-lg overflow-hidden',
        'bg-tactical-100 dark:bg-tactical-800',
        'border border-tactical-200 dark:border-tactical-700',
        className
      )}
      style={{ height }}
    >
      {/* Map background with shimmer */}
      <Skeleton
        variant="rectangular"
        className="absolute inset-0"
        animation="shimmer"
      />

      {/* Fake map markers */}
      <div className="absolute inset-0 p-4">
        <div className="relative w-full h-full">
          {/* Center marker */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <Skeleton variant="circular" className="w-8 h-8" animation="pulse" />
          </div>

          {/* Scattered markers */}
          <div className="absolute top-1/4 left-1/3">
            <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
          </div>
          <div className="absolute top-1/3 right-1/4">
            <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
          </div>
          <div className="absolute bottom-1/3 left-1/4">
            <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
          </div>
          <div className="absolute bottom-1/4 right-1/3">
            <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
          </div>
        </div>
      </div>

      {/* Loading overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-tactical-100/50 dark:bg-tactical-900/50">
        <div className="w-10 h-10 border-4 border-tiger-orange border-t-transparent rounded-full animate-spin mb-3" />
        <Skeleton variant="text" className="h-4 w-24" animation="none" />
      </div>
    </div>
  )
}

/**
 * Stats card skeleton
 */
export const StatCardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="stat-card-skeleton"
      className={cn('card', className)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <Skeleton variant="text" className="h-4 w-20 mb-2" />
          <Skeleton variant="text" className="h-9 w-24 mb-2" />
          <div className="flex items-center gap-1">
            <Skeleton variant="text" className="h-4 w-16" />
          </div>
        </div>
        <Skeleton variant="circular" className="w-10 h-10 flex-shrink-0" />
      </div>
    </div>
  )
}

/**
 * Tab navigation skeleton
 */
export const TabNavSkeleton = ({ className, count = 5 }: { className?: string; count?: number }) => {
  return (
    <div
      data-testid="tab-nav-skeleton"
      className={cn('flex gap-2 overflow-x-auto', className)}
    >
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="rounded" className="h-10 w-24 flex-shrink-0" />
      ))}
    </div>
  )
}

/**
 * Image quality panel skeleton
 */
export const ImageQualitySkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="image-quality-skeleton"
      className={cn('card', className)}
    >
      <div className="flex items-center gap-6">
        {/* Circular score */}
        <Skeleton variant="circular" className="w-24 h-24 flex-shrink-0" />

        {/* Metrics */}
        <div className="flex-1 space-y-3">
          {['Resolution', 'Sharpness', 'Stripe Visibility'].map((_, i) => (
            <div key={i} className="space-y-1">
              <Skeleton variant="text" className="h-4 w-24" />
              <Skeleton variant="rounded" className="h-2 w-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Ensemble visualization skeleton
 */
export const EnsembleSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="ensemble-skeleton"
      className={cn('space-y-3', className)}
    >
      <div className="flex items-center justify-between">
        <Skeleton variant="text" className="h-5 w-32" />
        <Skeleton variant="rounded" className="h-6 w-24" />
      </div>
      <Skeleton variant="rounded" className="h-4 w-full" />
      <div className="flex gap-2 flex-wrap">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} variant="rounded" className="h-6 w-20" />
        ))}
      </div>
    </div>
  )
}

/**
 * Table row skeleton
 */
export const TableRowSkeleton = ({ columns = 4, className }: { columns?: number; className?: string }) => {
  return (
    <div
      data-testid="table-row-skeleton"
      className={cn('flex items-center gap-4 py-3', className)}
    >
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} variant="text" className="h-4 flex-1" />
      ))}
    </div>
  )
}

/**
 * Investigation table row skeleton with proper layout
 */
export const InvestigationRowSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="investigation-row-skeleton"
      className={cn(
        'flex items-center gap-4 p-4',
        'bg-white dark:bg-tactical-800',
        'rounded-lg border border-tactical-200 dark:border-tactical-700',
        className
      )}
    >
      {/* Image thumbnail */}
      <Skeleton variant="rounded" className="w-12 h-12 flex-shrink-0" />

      {/* Date column */}
      <div className="flex-1 space-y-1.5 min-w-0">
        <Skeleton variant="text" className="h-4 w-24" />
        <Skeleton variant="text" className="h-3 w-16" />
      </div>

      {/* Status badge */}
      <Skeleton variant="rounded" className="h-6 w-20 flex-shrink-0" />

      {/* Match count */}
      <Skeleton variant="text" className="h-5 w-8 flex-shrink-0" />

      {/* Top match */}
      <div className="space-y-1 flex-shrink-0">
        <Skeleton variant="text" className="h-4 w-24" />
        <Skeleton variant="rounded" className="h-5 w-16" />
      </div>

      {/* Actions */}
      <div className="flex gap-2 flex-shrink-0">
        <Skeleton variant="rounded" className="h-8 w-8" />
        <Skeleton variant="rounded" className="h-8 w-8" />
      </div>
    </div>
  )
}

/**
 * Full investigation results skeleton
 */
export const InvestigationResultsSkeleton = () => {
  return (
    <div
      data-testid="investigation-results-skeleton"
      className="space-y-6 animate-fade-in-up"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton variant="text" className="h-8 w-64" />
          <Skeleton variant="text" className="h-4 w-48" />
        </div>
        <div className="flex gap-2">
          <Skeleton variant="rounded" className="h-10 w-32" />
          <Skeleton variant="rounded" className="h-10 w-24" />
        </div>
      </div>

      {/* Tab nav */}
      <TabNavSkeleton count={6} />

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>

      {/* Match cards */}
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <MatchCardSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

export default Skeleton
