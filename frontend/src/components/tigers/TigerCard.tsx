import { cn } from '../../utils/cn'
import Badge from '../common/Badge'
import { Skeleton } from '../common/Skeleton'
import {
  getConfidenceLevel,
  getConfidenceColors,
  normalizeScore,
  toPercentage,
  type ConfidenceLevel,
} from '../../utils/confidence'

/**
 * Tiger data structure for the card display
 */
export interface TigerCardData {
  id: string
  name: string
  image_path: string
  confidence_score: number
  status: 'verified' | 'pending' | 'unverified'
  facility?: {
    id: string
    name: string
  }
  created_at: string
}

/**
 * Props for the TigerCard component
 */
export interface TigerCardProps {
  tiger?: TigerCardData
  isSelected?: boolean
  onSelect?: (id: string) => void
  onClick?: (id: string) => void
  showCheckbox?: boolean
  isLoading?: boolean
  className?: string
}

/**
 * Status badge variant mapping
 */
const statusConfig: Record<
  TigerCardData['status'],
  { variant: 'success' | 'warning' | 'default'; label: string }
> = {
  verified: { variant: 'success', label: 'Verified' },
  pending: { variant: 'warning', label: 'Pending' },
  unverified: { variant: 'default', label: 'Unverified' },
}

/**
 * Confidence indicator dots component
 * Displays 5 dots representing confidence level
 */
function ConfidenceDots({
  score,
  level,
}: {
  score: number
  level: ConfidenceLevel
}) {
  const normalized = normalizeScore(score)
  // Calculate filled dots (1-5 based on score)
  const filledDots = Math.max(1, Math.min(5, Math.ceil(normalized * 5)))
  const colors = getConfidenceColors(level)

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((dot) => (
        <span
          key={dot}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            dot <= filledDots
              ? colors.bgSolid
              : 'bg-tactical-200 dark:bg-tactical-700'
          )}
        />
      ))}
    </div>
  )
}

/**
 * TigerCard skeleton for loading state
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
 * TigerCard component for displaying a single tiger in a grid
 *
 * Features:
 * - Selection checkbox for comparison
 * - Tiger image with fallback placeholder
 * - Facility name display
 * - Confidence score with visual indicator
 * - Status badge (verified/pending/unverified)
 * - Hover and selected states
 * - Loading skeleton state
 *
 * @example
 * ```tsx
 * <TigerCard
 *   tiger={tigerData}
 *   isSelected={selectedIds.includes(tigerData.id)}
 *   onSelect={(id) => toggleSelection(id)}
 *   onClick={(id) => navigate(`/tigers/${id}`)}
 *   showCheckbox
 * />
 *
 * // Loading state
 * <TigerCard isLoading />
 * ```
 */
export function TigerCard({
  tiger,
  isSelected = false,
  onSelect,
  onClick,
  showCheckbox = false,
  isLoading = false,
  className,
}: TigerCardProps) {
  // Show skeleton when loading
  if (isLoading || !tiger) {
    return <TigerCardSkeleton className={className} />
  }

  const { id, name, image_path, confidence_score, status, facility } = tiger
  const confidenceLevel = getConfidenceLevel(confidence_score)
  const confidenceColors = getConfidenceColors(confidenceLevel)
  const statusInfo = statusConfig[status]

  const handleCardClick = () => {
    if (onClick) {
      onClick(id)
    }
  }

  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onSelect) {
      onSelect(id)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleCardClick()
    }
  }

  return (
    <article
      data-testid="tiger-card"
      data-tiger-id={id}
      data-tiger-name={name}
      role="button"
      tabIndex={onClick ? 0 : undefined}
      onClick={handleCardClick}
      onKeyDown={onClick ? handleKeyDown : undefined}
      className={cn(
        // Base styles
        'relative flex flex-col rounded-xl overflow-hidden',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200/50 dark:border-tactical-700/50',
        'transition-all duration-200',
        // Hover styles
        onClick && [
          'cursor-pointer',
          'hover:shadow-lg hover:shadow-tactical-900/10',
          'hover:border-tactical-300 dark:hover:border-tactical-600',
        ],
        // Selected state
        isSelected && [
          'ring-2 ring-tiger-orange ring-offset-2',
          'dark:ring-offset-tactical-900',
          'border-tiger-orange dark:border-tiger-orange',
        ],
        className
      )}
    >
      {/* Header with checkbox and name */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-tactical-100 dark:border-tactical-700/50">
        {showCheckbox && (
          <div
            data-testid="tiger-card-select"
            onClick={handleCheckboxClick}
            className="flex-shrink-0"
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect?.(id)}
              onClick={(e) => e.stopPropagation()}
              aria-label={`Select ${name}`}
              className={cn(
                'w-4 h-4 rounded border-2 cursor-pointer',
                'border-tactical-300 dark:border-tactical-600',
                'text-tiger-orange focus:ring-tiger-orange focus:ring-offset-0',
                'transition-colors'
              )}
            />
          </div>
        )}
        <h3
          data-testid="tiger-card-name"
          className={cn(
            'flex-1 font-semibold text-sm truncate',
            'text-tactical-900 dark:text-tactical-100'
          )}
          title={name}
        >
          {name}
        </h3>
      </div>

      {/* Image container */}
      <div className="relative aspect-square bg-tactical-100 dark:bg-tactical-900">
        {image_path ? (
          <img
            data-testid="tiger-card-image"
            src={image_path}
            alt={`Photo of ${name}`}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              // Hide broken image and show placeholder
              const target = e.target as HTMLImageElement
              target.style.display = 'none'
              const placeholder = target.nextElementSibling as HTMLElement
              if (placeholder) {
                placeholder.style.display = 'flex'
              }
            }}
          />
        ) : null}
        {/* Fallback placeholder */}
        <div
          data-testid="tiger-card-image"
          className={cn(
            'absolute inset-0 flex items-center justify-center',
            'bg-tactical-100 dark:bg-tactical-900',
            image_path && 'hidden'
          )}
          style={{ display: image_path ? 'none' : 'flex' }}
        >
          <svg
            className="w-16 h-16 text-tactical-300 dark:text-tactical-700"
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
      </div>

      {/* Card footer with details */}
      <div className="flex flex-col gap-2 px-3 py-3">
        {/* Facility name */}
        {facility ? (
          <p
            data-testid="tiger-card-facility"
            className="text-xs text-tactical-600 dark:text-tactical-400 truncate"
            title={facility.name}
          >
            {facility.name}
          </p>
        ) : (
          <p
            data-testid="tiger-card-facility"
            className="text-xs text-tactical-400 dark:text-tactical-500 italic"
          >
            No facility
          </p>
        )}

        {/* Confidence score with dots */}
        <div
          data-testid="tiger-card-confidence"
          className="flex items-center justify-between gap-2"
        >
          <span
            className={cn('text-sm font-medium', confidenceColors.text)}
          >
            {toPercentage(confidence_score, 0)}
          </span>
          <ConfidenceDots score={confidence_score} level={confidenceLevel} />
        </div>

        {/* Status badge */}
        <div className="flex justify-start">
          <Badge
            data-testid="tiger-card-status"
            variant={statusInfo.variant}
            size="xs"
            dot
          >
            {statusInfo.label}
          </Badge>
        </div>
      </div>
    </article>
  )
}

export default TigerCard
