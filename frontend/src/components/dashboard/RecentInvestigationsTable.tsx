import { useState, useMemo } from 'react'
import { cn } from '../../utils/cn'
import Badge, { ConfidenceBadge } from '../common/Badge'
import Button from '../common/Button'
import { Skeleton } from '../common/Skeleton'
import EmptyState from '../common/EmptyState'
import {
  EyeIcon,
  TrashIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline'

// Types
export type InvestigationStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

export interface Investigation {
  id: string
  createdAt: string
  status: InvestigationStatus
  queryImageUrl?: string
  matchCount: number
  topMatchConfidence?: number
  topMatchTigerName?: string
  phase?: string
}

export interface RecentInvestigationsTableProps {
  investigations: Investigation[]
  maxRows?: number
  onViewInvestigation: (id: string) => void
  onDeleteInvestigation?: (id: string) => void
  isLoading?: boolean
  className?: string
}

// Sort configuration
type SortField = 'createdAt' | 'status' | 'matchCount' | 'topMatchConfidence'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  field: SortField
  direction: SortDirection
}

// Status badge variant mapping
const statusBadgeVariant: Record<InvestigationStatus, 'warning' | 'info' | 'success' | 'danger'> = {
  pending: 'warning',
  in_progress: 'info',
  completed: 'success',
  failed: 'danger',
}

const statusLabels: Record<InvestigationStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
  failed: 'Failed',
}

// Utility functions
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  const diffWeeks = Math.floor(diffDays / 7)

  if (diffSeconds < 60) {
    return 'Just now'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`
  } else if (diffHours < 24) {
    return `${diffHours}h ago`
  } else if (diffDays < 7) {
    return `${diffDays}d ago`
  } else if (diffWeeks < 4) {
    return `${diffWeeks}w ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }
}

const formatFullDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Sort icon component
const SortIcon = ({
  field,
  currentSort,
}: {
  field: SortField
  currentSort: SortConfig
}) => {
  if (currentSort.field !== field) {
    return (
      <ChevronUpIcon className="w-3.5 h-3.5 text-tactical-300 dark:text-tactical-600 opacity-0 group-hover:opacity-100 transition-opacity" />
    )
  }

  return currentSort.direction === 'asc' ? (
    <ChevronUpIcon className="w-3.5 h-3.5 text-tiger-orange" />
  ) : (
    <ChevronDownIcon className="w-3.5 h-3.5 text-tiger-orange" />
  )
}

// Table header cell with sorting
const SortableHeader = ({
  label,
  field,
  currentSort,
  onSort,
  className,
}: {
  label: string
  field: SortField
  currentSort: SortConfig
  onSort: (field: SortField) => void
  className?: string
}) => (
  <button
    type="button"
    onClick={() => onSort(field)}
    className={cn(
      'group flex items-center gap-1 text-xs font-semibold uppercase tracking-wide',
      'text-tactical-500 dark:text-tactical-400',
      'hover:text-tactical-700 dark:hover:text-tactical-300',
      'transition-colors',
      className
    )}
    data-testid={`sort-header-${field}`}
  >
    {label}
    <SortIcon field={field} currentSort={currentSort} />
  </button>
)

// Loading skeleton with shimmer animation
const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div data-testid="investigations-table-skeleton" className="space-y-2">
    {/* Header skeleton */}
    <div className="hidden lg:grid grid-cols-[60px_1fr_100px_100px_180px_120px] gap-4 px-4 py-3 border-b border-tactical-200 dark:border-tactical-700">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} variant="text" className="h-4 w-full" animation="shimmer" />
      ))}
    </div>

    {/* Row skeletons */}
    {Array.from({ length: rows }).map((_, i) => (
      <div
        key={i}
        data-testid={`investigation-row-skeleton-${i}`}
        className="flex items-center gap-4 p-4 bg-white dark:bg-tactical-800 rounded-lg border border-tactical-200 dark:border-tactical-700"
      >
        {/* Image thumbnail */}
        <Skeleton variant="rounded" className="w-12 h-12 flex-shrink-0" animation="shimmer" />

        {/* Date column */}
        <div className="flex-1 space-y-1.5 min-w-0">
          <Skeleton variant="text" className="h-4 w-24" animation="shimmer" />
          <Skeleton variant="text" className="h-3 w-16" animation="shimmer" />
        </div>

        {/* Status badge */}
        <Skeleton variant="rounded" className="h-6 w-20 flex-shrink-0" animation="shimmer" />

        {/* Match count */}
        <Skeleton variant="text" className="h-5 w-8 flex-shrink-0" animation="shimmer" />

        {/* Top match */}
        <div className="space-y-1 flex-shrink-0">
          <Skeleton variant="text" className="h-4 w-24" animation="shimmer" />
          <Skeleton variant="rounded" className="h-5 w-16" animation="shimmer" />
        </div>

        {/* Actions */}
        <div className="flex gap-2 flex-shrink-0">
          <Skeleton variant="rounded" className="h-8 w-8" animation="shimmer" />
          <Skeleton variant="rounded" className="h-8 w-8" animation="shimmer" />
        </div>
      </div>
    ))}
  </div>
)

// Main component
export const RecentInvestigationsTable = ({
  investigations,
  maxRows,
  onViewInvestigation,
  onDeleteInvestigation,
  isLoading = false,
  className,
}: RecentInvestigationsTableProps) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'createdAt',
    direction: 'desc',
  })
  const [statusFilter, setStatusFilter] = useState<InvestigationStatus | 'all'>('all')
  const [showFilters, setShowFilters] = useState(false)

  // Handle sorting
  const handleSort = (field: SortField) => {
    setSortConfig((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc',
    }))
  }

  // Filter and sort data
  const processedInvestigations = useMemo(() => {
    let result = [...investigations]

    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter((inv) => inv.status === statusFilter)
    }

    // Apply sorting
    result.sort((a, b) => {
      const direction = sortConfig.direction === 'asc' ? 1 : -1

      switch (sortConfig.field) {
        case 'createdAt':
          return direction * (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
        case 'status':
          return direction * a.status.localeCompare(b.status)
        case 'matchCount':
          return direction * (a.matchCount - b.matchCount)
        case 'topMatchConfidence':
          return direction * ((a.topMatchConfidence || 0) - (b.topMatchConfidence || 0))
        default:
          return 0
      }
    })

    // Apply max rows limit
    if (maxRows && maxRows > 0) {
      result = result.slice(0, maxRows)
    }

    return result
  }, [investigations, statusFilter, sortConfig, maxRows])

  // Loading state
  if (isLoading) {
    return <TableSkeleton rows={maxRows || 5} />
  }

  // Empty state
  if (investigations.length === 0) {
    return (
      <EmptyState
        icon={<MagnifyingGlassIcon className="w-6 h-6" />}
        title="No investigations yet"
        description="Start a new investigation by uploading a tiger image."
        className={className}
        data-testid="investigations-table-empty"
      />
    )
  }

  // Filtered empty state
  if (processedInvestigations.length === 0 && statusFilter !== 'all') {
    return (
      <div className={cn('space-y-4', className)} data-testid="investigations-table">
        {/* Filter controls */}
        <FilterControls
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
        />

        <EmptyState
          icon={<FunnelIcon className="w-6 h-6" />}
          title="No matching investigations"
          description={`No investigations with status "${statusLabels[statusFilter]}". Try changing your filter.`}
          action={{
            label: 'Clear filter',
            onClick: () => setStatusFilter('all'),
          }}
          size="sm"
        />
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)} data-testid="investigations-table">
      {/* Filter controls */}
      <FilterControls
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        showFilters={showFilters}
        setShowFilters={setShowFilters}
      />

      {/* Table */}
      <div className="overflow-x-auto">
        {/* Table Header */}
        <div
          className="hidden lg:grid grid-cols-[60px_1fr_100px_100px_180px_120px] gap-4 px-4 py-3 border-b border-tactical-200 dark:border-tactical-700"
          data-testid="table-header"
        >
          <div className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
            Image
          </div>
          <SortableHeader
            label="Date"
            field="createdAt"
            currentSort={sortConfig}
            onSort={handleSort}
          />
          <SortableHeader
            label="Status"
            field="status"
            currentSort={sortConfig}
            onSort={handleSort}
          />
          <SortableHeader
            label="Matches"
            field="matchCount"
            currentSort={sortConfig}
            onSort={handleSort}
          />
          <SortableHeader
            label="Top Match"
            field="topMatchConfidence"
            currentSort={sortConfig}
            onSort={handleSort}
          />
          <div className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide text-right">
            Actions
          </div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-tactical-100 dark:divide-tactical-800">
          {processedInvestigations.map((investigation) => (
            <InvestigationRow
              key={investigation.id}
              investigation={investigation}
              onView={onViewInvestigation}
              onDelete={onDeleteInvestigation}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

// Filter controls component
const FilterControls = ({
  statusFilter,
  setStatusFilter,
  showFilters,
  setShowFilters,
}: {
  statusFilter: InvestigationStatus | 'all'
  setStatusFilter: (status: InvestigationStatus | 'all') => void
  showFilters: boolean
  setShowFilters: (show: boolean) => void
}) => {
  const statusOptions: Array<{ value: InvestigationStatus | 'all'; label: string }> = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
  ]

  return (
    <div className="flex items-center justify-between">
      <button
        type="button"
        onClick={() => setShowFilters(!showFilters)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg',
          'text-tactical-600 dark:text-tactical-400',
          'hover:bg-tactical-100 dark:hover:bg-tactical-800',
          'transition-colors',
          showFilters && 'bg-tactical-100 dark:bg-tactical-800'
        )}
        data-testid="toggle-filters"
      >
        <FunnelIcon className="w-4 h-4" />
        Filters
        {statusFilter !== 'all' && (
          <span className="px-1.5 py-0.5 text-xs bg-tiger-orange text-white rounded-full">
            1
          </span>
        )}
      </button>

      {showFilters && (
        <div className="flex items-center gap-2" data-testid="status-filter">
          <span className="text-xs text-tactical-500 dark:text-tactical-400">Status:</span>
          <div className="flex gap-1">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setStatusFilter(option.value)}
                className={cn(
                  'px-2.5 py-1 text-xs font-medium rounded-lg transition-colors',
                  statusFilter === option.value
                    ? 'bg-tiger-orange text-white'
                    : 'bg-tactical-100 dark:bg-tactical-800 text-tactical-600 dark:text-tactical-400 hover:bg-tactical-200 dark:hover:bg-tactical-700'
                )}
                data-testid={`filter-${option.value}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Individual row component
const InvestigationRow = ({
  investigation,
  onView,
  onDelete,
}: {
  investigation: Investigation
  onView: (id: string) => void
  onDelete?: (id: string) => void
}) => {
  const handleRowClick = () => {
    onView(investigation.id)
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDelete) {
      onDelete(investigation.id)
    }
  }

  const handleViewClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onView(investigation.id)
  }

  return (
    <div
      className={cn(
        'grid grid-cols-1 lg:grid-cols-[60px_1fr_100px_100px_180px_120px] gap-4',
        'p-4 bg-white dark:bg-tactical-800',
        'hover:bg-tactical-50 dark:hover:bg-tactical-750',
        'cursor-pointer transition-colors',
        'group'
      )}
      onClick={handleRowClick}
      data-testid={`investigation-row-${investigation.id}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleRowClick()
        }
      }}
    >
      {/* Query Image Thumbnail */}
      <div className="flex items-center">
        <div
          className={cn(
            'w-12 h-12 rounded-lg overflow-hidden',
            'bg-tactical-100 dark:bg-tactical-700',
            'flex items-center justify-center',
            'ring-1 ring-tactical-200 dark:ring-tactical-600'
          )}
          data-testid="query-image-thumbnail"
        >
          {investigation.queryImageUrl ? (
            <img
              src={investigation.queryImageUrl}
              alt="Query tiger"
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <PhotoIcon className="w-6 h-6 text-tactical-400 dark:text-tactical-500" />
          )}
        </div>
      </div>

      {/* Date */}
      <div className="flex flex-col justify-center min-w-0">
        <span
          className="text-sm font-medium text-tactical-900 dark:text-tactical-100"
          title={formatFullDate(investigation.createdAt)}
          data-testid="investigation-date"
        >
          {formatRelativeTime(investigation.createdAt)}
        </span>
        {investigation.phase && (
          <span className="text-xs text-tactical-500 dark:text-tactical-400 truncate">
            Phase: {investigation.phase}
          </span>
        )}
        {/* Mobile-only labels */}
        <span className="text-xs text-tactical-400 dark:text-tactical-500 lg:hidden">
          {formatFullDate(investigation.createdAt)}
        </span>
      </div>

      {/* Status */}
      <div className="flex items-center" data-testid="investigation-status">
        <Badge
          variant={statusBadgeVariant[investigation.status]}
          size="sm"
          dot
        >
          {statusLabels[investigation.status]}
        </Badge>
      </div>

      {/* Match Count */}
      <div className="flex items-center" data-testid="investigation-match-count">
        <span
          className={cn(
            'text-lg font-semibold',
            investigation.matchCount > 0
              ? 'text-tactical-900 dark:text-tactical-100'
              : 'text-tactical-400 dark:text-tactical-500'
          )}
        >
          {investigation.matchCount}
        </span>
        <span className="ml-1 text-xs text-tactical-500 dark:text-tactical-400 lg:hidden">
          matches
        </span>
      </div>

      {/* Top Match */}
      <div className="flex flex-col justify-center min-w-0" data-testid="investigation-top-match">
        {investigation.topMatchTigerName || investigation.topMatchConfidence ? (
          <>
            {investigation.topMatchTigerName && (
              <span className="text-sm font-medium text-tactical-900 dark:text-tactical-100 truncate">
                {investigation.topMatchTigerName}
              </span>
            )}
            {investigation.topMatchConfidence !== undefined && (
              <ConfidenceBadge
                score={investigation.topMatchConfidence}
                size="xs"
                showLabel={false}
              />
            )}
          </>
        ) : (
          <span className="text-sm text-tactical-400 dark:text-tactical-500">
            No matches
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-2" data-testid="investigation-actions">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleViewClick}
          title="View Investigation"
          data-testid={`view-investigation-${investigation.id}`}
        >
          <EyeIcon className="w-4 h-4" />
          <span className="sr-only">View</span>
        </Button>

        {onDelete && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDeleteClick}
            title="Delete Investigation"
            className="text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-opacity"
            data-testid={`delete-investigation-${investigation.id}`}
          >
            <TrashIcon className="w-4 h-4" />
            <span className="sr-only">Delete</span>
          </Button>
        )}
      </div>
    </div>
  )
}

export default RecentInvestigationsTable
