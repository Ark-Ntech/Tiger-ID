import React from 'react'
import { cn } from '../../utils/cn'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { Skeleton } from '../common/Skeleton'
import {
  ArrowRightIcon,
  PhotoIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

// Types
export interface RelatedInvestigation {
  id: string
  created_at: string
  status: 'completed' | 'running' | 'error'
  confidence: 'high' | 'medium' | 'low'
  match_count: number
  top_match?: {
    tiger_id: string
    tiger_name: string
    similarity: number
  }
  image_thumbnail?: string
}

export interface RelatedInvestigationsPanelProps {
  investigations: RelatedInvestigation[]
  title?: string
  entityType: 'tiger' | 'facility'
  entityId: string
  entityName: string
  onInvestigationClick?: (id: string) => void
  maxItems?: number
  showViewAll?: boolean
  onViewAll?: () => void
  loading?: boolean
  className?: string
}

// Helper to format investigation ID for display
const formatInvestigationId = (id: string): string => {
  if (id.startsWith('INV-')) return id
  // Create a display-friendly ID from UUID or other formats
  const shortId = id.slice(0, 8).toUpperCase()
  return `INV-${shortId}`
}

// Helper to format date
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

// Status badge component
const StatusBadge: React.FC<{ status: RelatedInvestigation['status'] }> = ({ status }) => {
  const configs = {
    completed: {
      variant: 'success' as const,
      icon: CheckCircleIcon,
      label: 'Completed',
    },
    running: {
      variant: 'info' as const,
      icon: ArrowPathIcon,
      label: 'Running',
    },
    error: {
      variant: 'danger' as const,
      icon: ExclamationCircleIcon,
      label: 'Error',
    },
  }

  const config = configs[status]
  const Icon = config.icon

  return (
    <Badge variant={config.variant} size="xs" className="inline-flex items-center gap-1">
      <Icon className={cn('w-3 h-3', status === 'running' && 'animate-spin')} />
      {config.label}
    </Badge>
  )
}

// Confidence badge component
const ConfidenceBadge: React.FC<{ confidence: RelatedInvestigation['confidence'] }> = ({
  confidence,
}) => {
  const configs = {
    high: { variant: 'success' as const, label: 'High Confidence' },
    medium: { variant: 'warning' as const, label: 'Medium Confidence' },
    low: { variant: 'orange' as const, label: 'Low Confidence' },
  }

  const config = configs[confidence]

  return (
    <Badge variant={config.variant} size="xs">
      {config.label}
    </Badge>
  )
}

// Skeleton loader for investigation items
const InvestigationItemSkeleton: React.FC = () => (
  <div className="p-3 rounded-lg border border-tactical-200 dark:border-tactical-700 bg-white dark:bg-tactical-800">
    <div className="flex items-center gap-3">
      {/* Thumbnail skeleton */}
      <Skeleton variant="rounded" className="w-12 h-12 flex-shrink-0" />

      {/* Content skeleton */}
      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton variant="text" className="h-4 w-24" />
          <Skeleton variant="text" className="h-4 w-16" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton variant="rounded" className="h-5 w-16" />
          <Skeleton variant="rounded" className="h-5 w-14" />
        </div>
        <Skeleton variant="text" className="h-3 w-32" />
      </div>
    </div>
  </div>
)

// Individual investigation item
const InvestigationItem: React.FC<{
  investigation: RelatedInvestigation
  onClick?: () => void
}> = ({ investigation, onClick }) => {
  const isClickable = investigation.status !== 'running'

  return (
    <div
      data-testid={`related-investigation-${investigation.id}`}
      className={cn(
        'p-3 rounded-lg border transition-all duration-200',
        'border-tactical-200 dark:border-tactical-700',
        'bg-white dark:bg-tactical-800',
        isClickable && onClick && [
          'cursor-pointer',
          'hover:border-tactical-300 dark:hover:border-tactical-600',
          'hover:shadow-sm',
        ]
      )}
      onClick={isClickable && onClick ? onClick : undefined}
      role={isClickable && onClick ? 'button' : undefined}
      tabIndex={isClickable && onClick ? 0 : undefined}
      onKeyDown={
        isClickable && onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick()
              }
            }
          : undefined
      }
    >
      <div className="flex items-center gap-3">
        {/* Thumbnail */}
        <div className="relative flex-shrink-0">
          {investigation.image_thumbnail ? (
            <img
              src={investigation.image_thumbnail}
              alt="Investigation thumbnail"
              className="w-12 h-12 object-cover rounded-lg border border-tactical-200 dark:border-tactical-600"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none'
                const placeholder = (e.target as HTMLImageElement).nextElementSibling
                if (placeholder) {
                  ;(placeholder as HTMLElement).style.display = 'flex'
                }
              }}
            />
          ) : null}
          <div
            className={cn(
              'w-12 h-12 rounded-lg border border-tactical-200 dark:border-tactical-600',
              'bg-tactical-100 dark:bg-tactical-700',
              'items-center justify-center',
              investigation.image_thumbnail ? 'hidden' : 'flex'
            )}
          >
            <PhotoIcon className="w-5 h-5 text-tactical-400" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-tactical-900 dark:text-tactical-100">
              {formatInvestigationId(investigation.id)}
            </span>
            <span className="text-xs text-tactical-500 dark:text-tactical-400 flex items-center gap-1">
              <ClockIcon className="w-3 h-3" />
              {formatDate(investigation.created_at)}
            </span>
          </div>

          {/* Status and match count row */}
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <StatusBadge status={investigation.status} />
            {investigation.status === 'completed' && (
              <>
                <span className="text-xs text-tactical-600 dark:text-tactical-400">
                  {investigation.match_count} match{investigation.match_count !== 1 ? 'es' : ''}
                </span>
              </>
            )}
          </div>

          {/* Top match or processing status */}
          <div className="mt-1.5">
            {investigation.status === 'running' ? (
              <span className="text-xs text-blue-600 dark:text-blue-400 italic">
                Processing...
              </span>
            ) : investigation.status === 'error' ? (
              <span className="text-xs text-red-600 dark:text-red-400">
                Investigation failed
              </span>
            ) : investigation.top_match ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-tactical-600 dark:text-tactical-400">
                  Top: {investigation.top_match.tiger_name} ({Math.round(investigation.top_match.similarity * 100)}%)
                </span>
                <ConfidenceBadge confidence={investigation.confidence} />
              </div>
            ) : (
              <span className="text-xs text-tactical-500 dark:text-tactical-400">
                No matches found
              </span>
            )}
          </div>
        </div>

        {/* Arrow indicator for clickable items */}
        {isClickable && onClick && (
          <ArrowRightIcon className="w-4 h-4 text-tactical-400 flex-shrink-0" />
        )}
      </div>
    </div>
  )
}

// Empty state component
const EmptyState: React.FC<{ entityType: 'tiger' | 'facility'; entityName: string }> = ({
  entityType,
  entityName,
}) => (
  <div
    data-testid="related-investigations-empty"
    className={cn(
      'py-8 px-4 text-center rounded-lg',
      'bg-tactical-50 dark:bg-tactical-900/50',
      'border border-dashed border-tactical-300 dark:border-tactical-700'
    )}
  >
    <PhotoIcon className="w-10 h-10 mx-auto text-tactical-400 mb-3" />
    <p className="text-sm text-tactical-600 dark:text-tactical-400">
      No investigations found for this {entityType}
    </p>
    <p className="text-xs text-tactical-500 dark:text-tactical-500 mt-1">
      Run an investigation to analyze {entityName}
    </p>
  </div>
)

// Main component
export const RelatedInvestigationsPanel: React.FC<RelatedInvestigationsPanelProps> = ({
  investigations,
  title = 'Related Investigations',
  entityType,
  entityId: _entityId,
  entityName,
  onInvestigationClick,
  maxItems = 5,
  showViewAll = true,
  onViewAll,
  loading = false,
  className,
}) => {
  // entityId is available for future use (e.g., API calls, analytics)
  void _entityId
  const displayedInvestigations = investigations.slice(0, maxItems)
  const hasMore = investigations.length > maxItems
  const totalCount = investigations.length

  return (
    <Card
      data-testid="related-investigations-panel"
      variant="default"
      padding="none"
      className={className}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-tactical-200 dark:border-tactical-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3
            data-testid="related-investigations-title"
            className="font-semibold text-tactical-900 dark:text-tactical-100"
          >
            {title}
          </h3>
          {!loading && (
            <span
              data-testid="related-investigations-count"
              className={cn(
                'text-xs font-medium px-2 py-0.5 rounded-full',
                'bg-tactical-100 text-tactical-600',
                'dark:bg-tactical-700 dark:text-tactical-300'
              )}
            >
              {totalCount}
            </span>
          )}
        </div>

        {showViewAll && !loading && hasMore && onViewAll && (
          <button
            data-testid="related-investigations-view-all"
            onClick={onViewAll}
            className={cn(
              'text-sm font-medium text-tiger-orange hover:text-tiger-orange-dark',
              'dark:text-tiger-orange-light dark:hover:text-tiger-orange',
              'inline-flex items-center gap-1 transition-colors'
            )}
          >
            View All
            <ArrowRightIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Content */}
      <div
        data-testid="related-investigations-list"
        className="p-4 space-y-3"
      >
        {loading ? (
          // Loading skeletons
          <>
            <InvestigationItemSkeleton />
            <InvestigationItemSkeleton />
            <InvestigationItemSkeleton />
          </>
        ) : displayedInvestigations.length === 0 ? (
          // Empty state
          <EmptyState entityType={entityType} entityName={entityName} />
        ) : (
          // Investigation list
          displayedInvestigations.map((investigation) => (
            <InvestigationItem
              key={investigation.id}
              investigation={investigation}
              onClick={
                onInvestigationClick
                  ? () => onInvestigationClick(investigation.id)
                  : undefined
              }
            />
          ))
        )}
      </div>

      {/* Footer with view all (alternative placement) */}
      {showViewAll && !loading && hasMore && onViewAll && (
        <div className="px-4 py-3 border-t border-tactical-200 dark:border-tactical-700 bg-tactical-50 dark:bg-tactical-900/30">
          <button
            onClick={onViewAll}
            className={cn(
              'w-full text-sm font-medium py-2 rounded-lg transition-colors',
              'text-tactical-600 hover:text-tactical-900 hover:bg-tactical-100',
              'dark:text-tactical-400 dark:hover:text-tactical-100 dark:hover:bg-tactical-800'
            )}
          >
            View all {totalCount} investigations
          </button>
        </div>
      )}
    </Card>
  )
}

export default RelatedInvestigationsPanel
