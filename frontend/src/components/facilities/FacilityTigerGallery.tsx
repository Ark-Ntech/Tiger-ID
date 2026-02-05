import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { cn } from '../../utils/cn'
import Badge, { ConfidenceBadge } from '../common/Badge'
import { Skeleton } from '../common/Skeleton'
import EmptyState from '../common/EmptyState'
import { normalizeScore } from '../../utils/confidence'

/**
 * Tiger image data structure for gallery display
 */
export interface TigerImage {
  id: string
  tigerId: string
  tigerName?: string
  imageUrl: string
  thumbnailUrl?: string
  captureDate?: string
  confidence?: number
  qualityScore?: number
}

/**
 * Props for the FacilityTigerGallery component
 */
export interface FacilityTigerGalleryProps {
  /** Unique identifier of the facility */
  facilityId: string
  /** Display name of the facility */
  facilityName: string
  /** Array of tiger images to display */
  images: TigerImage[]
  /** Callback when an image is clicked */
  onImageClick?: (image: TigerImage) => void
  /** Callback when a tiger name/link is clicked */
  onTigerClick?: (tigerId: string) => void
  /** Display mode: grid or list */
  viewMode?: 'grid' | 'list'
  /** Whether to group images by tiger */
  groupByTiger?: boolean
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Quality indicator thresholds
 */
const QUALITY_THRESHOLDS = {
  EXCELLENT: 0.9,
  GOOD: 0.7,
  FAIR: 0.5,
} as const

/**
 * Get quality indicator color and label
 */
function getQualityIndicator(score: number): {
  color: string
  bgColor: string
  label: string
} {
  const normalized = normalizeScore(score)
  if (normalized >= QUALITY_THRESHOLDS.EXCELLENT) {
    return {
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-500',
      label: 'Excellent',
    }
  }
  if (normalized >= QUALITY_THRESHOLDS.GOOD) {
    return {
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-500',
      label: 'Good',
    }
  }
  if (normalized >= QUALITY_THRESHOLDS.FAIR) {
    return {
      color: 'text-amber-600 dark:text-amber-400',
      bgColor: 'bg-amber-500',
      label: 'Fair',
    }
  }
  return {
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-500',
    label: 'Poor',
  }
}

/**
 * Lazy loaded image component with intersection observer
 */
function LazyImage({
  src,
  alt,
  className,
  onLoad,
  onError,
}: {
  src: string
  alt: string
  className?: string
  onLoad?: () => void
  onError?: () => void
}) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '100px',
        threshold: 0.01,
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    return () => observer.disconnect()
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  return (
    <div ref={imgRef} className={cn('relative overflow-hidden', className)}>
      {/* Placeholder while loading */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-tactical-100 dark:bg-tactical-800 animate-pulse flex items-center justify-center">
          <svg
            className="w-8 h-8 text-tactical-300 dark:text-tactical-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 bg-tactical-100 dark:bg-tactical-800 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-tactical-400 dark:text-tactical-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
      )}

      {/* Actual image */}
      {isInView && !hasError && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={handleLoad}
          onError={handleError}
          className={cn(
            'w-full h-full object-cover transition-opacity duration-300',
            isLoaded ? 'opacity-100' : 'opacity-0'
          )}
        />
      )}
    </div>
  )
}

/**
 * Quality indicator overlay component
 */
function QualityOverlay({ score }: { score: number }) {
  const quality = getQualityIndicator(score)
  return (
    <div
      data-testid="quality-overlay"
      className={cn(
        'absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1',
        'bg-tactical-900/70 backdrop-blur-sm rounded-full',
        'text-xs font-medium'
      )}
    >
      <span className={cn('w-2 h-2 rounded-full', quality.bgColor)} />
      <span className="text-white">{quality.label}</span>
    </div>
  )
}

/**
 * Single image card for grid view
 */
function ImageCard({
  image,
  onImageClick,
  onTigerClick,
}: {
  image: TigerImage
  onImageClick?: (image: TigerImage) => void
  onTigerClick?: (tigerId: string) => void
}) {
  const handleImageClick = () => {
    onImageClick?.(image)
  }

  const handleTigerClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onTigerClick?.(image.tigerId)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleImageClick()
    }
  }

  return (
    <article
      data-testid="image-card"
      data-image-id={image.id}
      role={onImageClick ? 'button' : undefined}
      tabIndex={onImageClick ? 0 : undefined}
      onClick={handleImageClick}
      onKeyDown={onImageClick ? handleKeyDown : undefined}
      className={cn(
        'relative rounded-xl overflow-hidden',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200/50 dark:border-tactical-700/50',
        'transition-all duration-200',
        onImageClick && [
          'cursor-pointer',
          'hover:shadow-lg hover:shadow-tactical-900/10',
          'hover:border-tactical-300 dark:hover:border-tactical-600',
        ]
      )}
    >
      {/* Image container */}
      <div className="relative aspect-square">
        <LazyImage
          src={image.thumbnailUrl || image.imageUrl}
          alt={image.tigerName ? `Photo of ${image.tigerName}` : 'Tiger photo'}
          className="w-full h-full"
        />

        {/* Quality indicator overlay */}
        {image.qualityScore !== undefined && (
          <QualityOverlay score={image.qualityScore} />
        )}

        {/* Confidence badge overlay */}
        {image.confidence !== undefined && (
          <div className="absolute top-2 right-2">
            <ConfidenceBadge score={image.confidence} size="xs" />
          </div>
        )}

        {/* Hover overlay */}
        <div
          className={cn(
            'absolute inset-0 bg-tactical-900/0 transition-colors duration-200',
            onImageClick && 'group-hover:bg-tactical-900/30'
          )}
        />
      </div>

      {/* Card footer */}
      <div className="px-3 py-2 border-t border-tactical-100 dark:border-tactical-700/50">
        {/* Tiger name */}
        {image.tigerName ? (
          <button
            data-testid="tiger-name-link"
            type="button"
            onClick={handleTigerClick}
            className={cn(
              'text-sm font-medium truncate block w-full text-left',
              'text-tactical-900 dark:text-tactical-100',
              onTigerClick && [
                'hover:text-tiger-orange dark:hover:text-tiger-orange-light',
                'transition-colors cursor-pointer',
              ]
            )}
          >
            {image.tigerName}
          </button>
        ) : (
          <span className="text-sm text-tactical-400 dark:text-tactical-500 italic">
            Unknown tiger
          </span>
        )}

        {/* Capture date */}
        {image.captureDate && (
          <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
            {new Date(image.captureDate).toLocaleDateString()}
          </p>
        )}
      </div>
    </article>
  )
}

/**
 * Single image row for list view
 */
function ImageRow({
  image,
  onImageClick,
  onTigerClick,
}: {
  image: TigerImage
  onImageClick?: (image: TigerImage) => void
  onTigerClick?: (tigerId: string) => void
}) {
  const handleImageClick = () => {
    onImageClick?.(image)
  }

  const handleTigerClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onTigerClick?.(image.tigerId)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleImageClick()
    }
  }

  return (
    <article
      data-testid="image-row"
      data-image-id={image.id}
      role={onImageClick ? 'button' : undefined}
      tabIndex={onImageClick ? 0 : undefined}
      onClick={handleImageClick}
      onKeyDown={onImageClick ? handleKeyDown : undefined}
      className={cn(
        'flex items-center gap-4 p-3',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200/50 dark:border-tactical-700/50',
        'rounded-xl transition-all duration-200',
        onImageClick && [
          'cursor-pointer',
          'hover:shadow-md hover:border-tactical-300 dark:hover:border-tactical-600',
        ]
      )}
    >
      {/* Thumbnail */}
      <div className="relative w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden">
        <LazyImage
          src={image.thumbnailUrl || image.imageUrl}
          alt={image.tigerName ? `Photo of ${image.tigerName}` : 'Tiger photo'}
          className="w-full h-full"
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Tiger name */}
        {image.tigerName ? (
          <button
            data-testid="tiger-name-link"
            type="button"
            onClick={handleTigerClick}
            className={cn(
              'text-sm font-medium truncate block text-left',
              'text-tactical-900 dark:text-tactical-100',
              onTigerClick && [
                'hover:text-tiger-orange dark:hover:text-tiger-orange-light',
                'transition-colors cursor-pointer',
              ]
            )}
          >
            {image.tigerName}
          </button>
        ) : (
          <span className="text-sm text-tactical-400 dark:text-tactical-500 italic">
            Unknown tiger
          </span>
        )}

        {/* Capture date */}
        {image.captureDate && (
          <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
            {new Date(image.captureDate).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* Quality indicator */}
      {image.qualityScore !== undefined && (
        <div className="flex-shrink-0">
          {(() => {
            const quality = getQualityIndicator(image.qualityScore)
            return (
              <Badge
                data-testid="quality-badge"
                variant="default"
                size="xs"
                className={quality.color}
              >
                {quality.label}
              </Badge>
            )
          })()}
        </div>
      )}

      {/* Confidence badge */}
      {image.confidence !== undefined && (
        <div className="flex-shrink-0">
          <ConfidenceBadge score={image.confidence} size="xs" />
        </div>
      )}
    </article>
  )
}

/**
 * Collapsible tiger section for grouped view
 */
function TigerSection({
  tigerId,
  tigerName,
  images,
  viewMode,
  onImageClick,
  onTigerClick,
  defaultExpanded = true,
}: {
  tigerId: string
  tigerName: string
  images: TigerImage[]
  viewMode: 'grid' | 'list'
  onImageClick?: (image: TigerImage) => void
  onTigerClick?: (tigerId: string) => void
  defaultExpanded?: boolean
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  const handleToggle = () => {
    setIsExpanded((prev) => !prev)
  }

  const handleTigerClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onTigerClick?.(tigerId)
  }

  // Calculate average confidence for the section
  const avgConfidence = useMemo(() => {
    const scores = images
      .filter((img) => img.confidence !== undefined)
      .map((img) => normalizeScore(img.confidence!))
    if (scores.length === 0) return undefined
    return scores.reduce((a, b) => a + b, 0) / scores.length
  }, [images])

  return (
    <section
      data-testid="tiger-section"
      data-tiger-id={tigerId}
      className="rounded-xl border border-tactical-200/50 dark:border-tactical-700/50 overflow-hidden"
    >
      {/* Section header */}
      <button
        data-testid="tiger-section-header"
        type="button"
        onClick={handleToggle}
        className={cn(
          'w-full flex items-center justify-between px-4 py-3',
          'bg-tactical-50 dark:bg-tactical-800/50',
          'hover:bg-tactical-100 dark:hover:bg-tactical-700/50',
          'transition-colors'
        )}
      >
        <div className="flex items-center gap-3">
          {/* Expand/collapse icon */}
          <svg
            className={cn(
              'w-4 h-4 text-tactical-500 transition-transform duration-200',
              isExpanded && 'rotate-90'
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>

          {/* Tiger name */}
          <span
            data-testid="tiger-section-name"
            onClick={handleTigerClick}
            className={cn(
              'font-medium text-tactical-900 dark:text-tactical-100',
              onTigerClick && [
                'hover:text-tiger-orange dark:hover:text-tiger-orange-light',
                'cursor-pointer',
              ]
            )}
          >
            {tigerName}
          </span>

          {/* Image count */}
          <Badge variant="default" size="xs">
            {images.length} image{images.length !== 1 ? 's' : ''}
          </Badge>
        </div>

        {/* Average confidence */}
        {avgConfidence !== undefined && (
          <ConfidenceBadge score={avgConfidence} size="xs" />
        )}
      </button>

      {/* Section content */}
      {isExpanded && (
        <div
          data-testid="tiger-section-content"
          className={cn(
            'p-4 bg-white dark:bg-tactical-800',
            viewMode === 'grid'
              ? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
              : 'space-y-3'
          )}
        >
          {images.map((image) =>
            viewMode === 'grid' ? (
              <ImageCard
                key={image.id}
                image={image}
                onImageClick={onImageClick}
                onTigerClick={onTigerClick}
              />
            ) : (
              <ImageRow
                key={image.id}
                image={image}
                onImageClick={onImageClick}
                onTigerClick={onTigerClick}
              />
            )
          )}
        </div>
      )}
    </section>
  )
}

/**
 * Loading skeleton for grid view
 */
function GallerySkeleton({ viewMode }: { viewMode: 'grid' | 'list' }) {
  const itemCount = viewMode === 'grid' ? 8 : 5

  if (viewMode === 'grid') {
    return (
      <div
        data-testid="gallery-skeleton"
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
      >
        {Array.from({ length: itemCount }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-tactical-200/50 dark:border-tactical-700/50 overflow-hidden"
          >
            <Skeleton variant="rectangular" className="aspect-square w-full" />
            <div className="px-3 py-2 space-y-2">
              <Skeleton variant="text" className="h-4 w-3/4" />
              <Skeleton variant="text" className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div data-testid="gallery-skeleton" className="space-y-3">
      {Array.from({ length: itemCount }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-3 rounded-xl border border-tactical-200/50 dark:border-tactical-700/50"
        >
          <Skeleton variant="rounded" className="w-16 h-16 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" className="h-4 w-1/3" />
            <Skeleton variant="text" className="h-3 w-1/4" />
          </div>
          <Skeleton variant="rounded" className="h-6 w-16" />
        </div>
      ))}
    </div>
  )
}

/**
 * View mode toggle button
 */
function ViewModeToggle({
  viewMode,
  onChange,
}: {
  viewMode: 'grid' | 'list'
  onChange: (mode: 'grid' | 'list') => void
}) {
  return (
    <div
      data-testid="view-mode-toggle"
      className="flex items-center bg-tactical-100 dark:bg-tactical-700 rounded-lg p-1"
    >
      <button
        type="button"
        onClick={() => onChange('grid')}
        className={cn(
          'p-2 rounded-md transition-colors',
          viewMode === 'grid'
            ? 'bg-white dark:bg-tactical-600 text-tactical-900 dark:text-tactical-100 shadow-sm'
            : 'text-tactical-500 dark:text-tactical-400 hover:text-tactical-700 dark:hover:text-tactical-300'
        )}
        aria-label="Grid view"
        aria-pressed={viewMode === 'grid'}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
          />
        </svg>
      </button>
      <button
        type="button"
        onClick={() => onChange('list')}
        className={cn(
          'p-2 rounded-md transition-colors',
          viewMode === 'list'
            ? 'bg-white dark:bg-tactical-600 text-tactical-900 dark:text-tactical-100 shadow-sm'
            : 'text-tactical-500 dark:text-tactical-400 hover:text-tactical-700 dark:hover:text-tactical-300'
        )}
        aria-label="List view"
        aria-pressed={viewMode === 'list'}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
    </div>
  )
}

/**
 * Group by tiger toggle
 */
function GroupByToggle({
  groupByTiger,
  onChange,
}: {
  groupByTiger: boolean
  onChange: (grouped: boolean) => void
}) {
  return (
    <label
      data-testid="group-by-toggle"
      className="flex items-center gap-2 cursor-pointer"
    >
      <input
        type="checkbox"
        checked={groupByTiger}
        onChange={(e) => onChange(e.target.checked)}
        className={cn(
          'w-4 h-4 rounded border-2 cursor-pointer',
          'border-tactical-300 dark:border-tactical-600',
          'text-tiger-orange focus:ring-tiger-orange focus:ring-offset-0',
          'transition-colors'
        )}
      />
      <span className="text-sm text-tactical-600 dark:text-tactical-400">
        Group by tiger
      </span>
    </label>
  )
}

/**
 * FacilityTigerGallery component
 *
 * Displays a gallery of tiger images from a specific facility.
 * Supports grid/list view, grouping by tiger, and various interaction handlers.
 *
 * @example
 * ```tsx
 * <FacilityTigerGallery
 *   facilityId="facility-123"
 *   facilityName="Wildlife Sanctuary"
 *   images={tigerImages}
 *   onImageClick={(img) => openLightbox(img)}
 *   onTigerClick={(id) => navigate(`/tigers/${id}`)}
 *   viewMode="grid"
 *   groupByTiger
 * />
 * ```
 */
export function FacilityTigerGallery({
  facilityId,
  facilityName,
  images,
  onImageClick,
  onTigerClick,
  viewMode: initialViewMode = 'grid',
  groupByTiger: initialGroupByTiger = false,
  isLoading = false,
  className,
}: FacilityTigerGalleryProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(initialViewMode)
  const [groupByTiger, setGroupByTiger] = useState(initialGroupByTiger)

  // Group images by tiger
  const groupedImages = useMemo(() => {
    if (!groupByTiger) return null

    const groups: Map<string, { tigerName: string; images: TigerImage[] }> =
      new Map()

    images.forEach((image) => {
      const existing = groups.get(image.tigerId)
      if (existing) {
        existing.images.push(image)
      } else {
        groups.set(image.tigerId, {
          tigerName: image.tigerName || 'Unknown Tiger',
          images: [image],
        })
      }
    })

    // Sort groups by tiger name
    return Array.from(groups.entries()).sort((a, b) =>
      a[1].tigerName.localeCompare(b[1].tigerName)
    )
  }, [images, groupByTiger])

  // Handle view mode change
  const handleViewModeChange = useCallback((mode: 'grid' | 'list') => {
    setViewMode(mode)
  }, [])

  // Handle group by toggle
  const handleGroupByChange = useCallback((grouped: boolean) => {
    setGroupByTiger(grouped)
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <div
        data-testid="facility-tiger-gallery"
        data-facility-id={facilityId}
        className={cn('space-y-4', className)}
      >
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton variant="text" className="h-6 w-48" />
            <Skeleton variant="text" className="h-4 w-32" />
          </div>
          <div className="flex items-center gap-4">
            <Skeleton variant="rounded" className="h-10 w-32" />
            <Skeleton variant="rounded" className="h-10 w-20" />
          </div>
        </div>

        {/* Gallery skeleton */}
        <GallerySkeleton viewMode={viewMode} />
      </div>
    )
  }

  // Empty state
  if (images.length === 0) {
    return (
      <div
        data-testid="facility-tiger-gallery"
        data-facility-id={facilityId}
        className={cn('', className)}
      >
        <EmptyState
          data-testid="gallery-empty-state"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          }
          title="No tiger images found"
          description={`No tiger images have been associated with ${facilityName} yet.`}
          size="lg"
        />
      </div>
    )
  }

  return (
    <div
      data-testid="facility-tiger-gallery"
      data-facility-id={facilityId}
      className={cn('space-y-4', className)}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2
            data-testid="gallery-title"
            className="text-lg font-semibold text-tactical-900 dark:text-tactical-100"
          >
            Tiger Gallery
          </h2>
          <p
            data-testid="gallery-subtitle"
            className="text-sm text-tactical-600 dark:text-tactical-400"
          >
            {images.length} image{images.length !== 1 ? 's' : ''} from{' '}
            {facilityName}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <GroupByToggle
            groupByTiger={groupByTiger}
            onChange={handleGroupByChange}
          />
          <ViewModeToggle viewMode={viewMode} onChange={handleViewModeChange} />
        </div>
      </div>

      {/* Gallery content */}
      {groupByTiger && groupedImages ? (
        // Grouped view
        <div data-testid="grouped-gallery" className="space-y-4">
          {groupedImages.map(([tigerId, { tigerName, images: tigerImages }]) => (
            <TigerSection
              key={tigerId}
              tigerId={tigerId}
              tigerName={tigerName}
              images={tigerImages}
              viewMode={viewMode}
              onImageClick={onImageClick}
              onTigerClick={onTigerClick}
            />
          ))}
        </div>
      ) : viewMode === 'grid' ? (
        // Flat grid view
        <div
          data-testid="flat-gallery"
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
        >
          {images.map((image) => (
            <ImageCard
              key={image.id}
              image={image}
              onImageClick={onImageClick}
              onTigerClick={onTigerClick}
            />
          ))}
        </div>
      ) : (
        // Flat list view
        <div data-testid="flat-gallery" className="space-y-3">
          {images.map((image) => (
            <ImageRow
              key={image.id}
              image={image}
              onImageClick={onImageClick}
              onTigerClick={onTigerClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default FacilityTigerGallery
